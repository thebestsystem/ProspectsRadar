"""Scanner service: orchestrates deterministic 5-pillar scoring and auto-fix generation."""

import asyncio
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.repo.crawler import (
    HEADERS,
    fetch_llms_info,
    fetch_robots_info,
    fetch_web_page,
    normalize_scan_url,
)
from app.repo.parser_html import (
    analyze_semantic_purity,
    extract_price_from_html,
    extract_product_name,
    extract_stock_from_html,
)
from app.repo.parser_schema import analyze_schema, extract_json_ld
from app.types.scanner import AuditResult, BrokenItem, PillarScore, ProductData


def _generate_auto_fix(domain: str, prod: ProductData) -> dict[str, str]:
    """Generate ready-to-use snippets for llms.txt, Schema.org and MCP."""
    clean_domain = domain.lower().replace("www.", "")
    name = prod.name or f"Boutique {clean_domain}"
    sku = prod.sku or "SKU-01"
    price = prod.price if prod.price != "Inconnu" else "0.00"

    schema_json = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "{name}",
  "sku": "{sku}",
  "offers": {{
    "@type": "Offer",
    "price": "{price}",
    "priceCurrency": "{prod.currency}",
    "availability": "https://schema.org/InStock",
    "shippingDetails": {{
      "@type": "OfferShippingDetails",
      "shippingRate": {{ "@type": "MonetaryAmount", "value": "0.00", "currency": "{prod.currency}" }}
    }},
    "hasMerchantReturnPolicy": {{
      "@type": "MerchantReturnPolicy",
      "merchantReturnDays": 30,
      "returnFees": "https://schema.org/FreeReturn"
    }}
  }}
}}
</script>"""

    llms_txt = f"""# LLMS.txt pour {clean_domain}
# Specification: https://llmstxt.org/ v1.0
> {name} sur {clean_domain}.
- Fiche produit: [{name}](/products/{sku.lower()})
- Prix garanti: {price} {prod.currency}
- Expédition & retours conformes
- Contact IA: contact@{clean_domain}
"""

    mcp_config = f"""{{
  "mcpServers": {{
    "{clean_domain.replace('.', '-')}-agent": {{
      "command": "npx",
      "args": ["-y", "@agentready/mcp-server-commerce", "--store={clean_domain}"]
    }}
  }}
}}"""
    return {"schemaJson": schema_json, "llmsTxt": llms_txt, "mcpConfig": mcp_config}


async def audit_url(raw_url: str) -> AuditResult:
    """Execute complete deterministic 5-pillar audit on a URL."""
    url = normalize_scan_url(raw_url)
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    scheme = parsed.scheme or "https"

    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=12.0
    ) as client:
        robots_task = asyncio.create_task(fetch_robots_info(client, domain, scheme=scheme))
        llms_task = asyncio.create_task(fetch_llms_info(client, domain, scheme=scheme))

        try:
            status_code, headers_dict, html_content = await fetch_web_page(client, url)
        except Exception as e:
            await asyncio.gather(robots_task, llms_task, return_exceptions=True)
            raise ValueError(f"Impossible de joindre {domain} : {e}") from e

        robots_info, llms_info = await asyncio.gather(robots_task, llms_task)

    soup = BeautifulSoup(html_content, "html.parser")

    # Pilier 1 : Crawl & Bot Accessibility (20%)
    p1_score = 100
    p1_details = []
    is_cf = "cf-ray" in headers_dict or "cloudflare" in headers_dict.get("server", "").lower()
    is_waf_blocked = False
    if is_cf and status_code in (403, 503):
        p1_score = 25
        is_waf_blocked = True
        p1_details.append("Protection WAF Cloudflare Challenge active (Bots bloqués)")
    elif is_cf:
        p1_score -= 10
        p1_details.append("Cloudflare détecté (Accès standard préservé)")

    if not robots_info.get("found"):
        p1_score -= 15
        p1_details.append("robots.txt absent : sans directives d'indexation IA explicites")
    elif robots_info["global_disallowed"]:
        p1_score -= 50
        p1_details.append("robots.txt bloque tous les crawlers (Disallow: /)")
    elif robots_info["disallowed_bots"]:
        p1_score -= 30
        p1_details.append(f"robots.txt bloque : {', '.join(robots_info['disallowed_bots'])}")
    else:
        p1_details.append("robots.txt autorise les bots IA (GPTBot, ClaudeBot, PerplexityBot)")
    p1_score = max(10, min(100, p1_score))

    # Pilier 2 : Schema.org & JSON-LD (25%)
    json_ld_list = extract_json_ld(soup)
    schema_res = analyze_schema(json_ld_list)
    raw_prod = schema_res["product_data"]
    prod_data = ProductData(
        name=raw_prod.get("name") or extract_product_name(soup, domain),
        sku=raw_prod.get("sku") or f"{domain[:4].upper()}-01",
        price=raw_prod.get("price") or "Inconnu",
        currency=raw_prod.get("currency") or "EUR",
        has_shipping=bool(raw_prod.get("has_shipping")),
        has_return=bool(raw_prod.get("has_return")),
        has_stock=bool(raw_prod.get("has_stock")),
        description=raw_prod.get("description", ""),
        price_source=raw_prod.get("price_source"),
        stock_source=raw_prod.get("stock_source"),
    )

    if prod_data.price == "Inconnu":
        p_val, p_curr, p_src = extract_price_from_html(soup)
        if p_val:
            prod_data.price = p_val
            prod_data.currency = p_curr or "EUR"
            prod_data.price_source = "html"
            prod_data.price_detail = p_src

    if not prod_data.has_stock:
        h_stock = extract_stock_from_html(soup)
        if h_stock is not None:
            prod_data.has_stock = h_stock
            prod_data.stock_source = "html"

    # Pilier 3 : Pureté Sémantique & Tokens (20%)
    semantic_res = analyze_semantic_purity(soup, len(html_content))

    # Pilier 4 : Simulateur d'Acheteur IA (20%)
    p4_score = 30
    p4_details = []
    if prod_data.price != "Inconnu":
        p4_score += 25
        p4_details.append(f"Prix certifié : {prod_data.price} {prod_data.currency}")
    else:
        p4_details.append("Prix incertain ou masqué par JavaScript")
    if prod_data.has_shipping:
        p4_score += 20
        p4_details.append("Livraison structurée (0 hallucination sur les frais)")
    else:
        p4_details.append("Frais de livraison absents : Risque d'hallucination")
    if prod_data.has_return:
        p4_score += 15
        p4_details.append("Politique de retour validée")
    if prod_data.has_stock:
        p4_score += 10
        p4_details.append("Disponibilité en stock validée")
    p4_score = min(100, p4_score)

    # Pilier 5 : Protocoles Agentiques (15%)
    p5_score = 5
    p5_details = []
    if llms_info.get("found"):
        p5_score = 70 if llms_info["path"] == "/.well-known/llms.txt" else 45
        p5_details.append(f"Manifeste {llms_info['path']} détecté")
        if "mcp" in (llms_info.get("content") or "").lower():
            p5_score += 30
            p5_details.append("Directives MCP trouvées dans le manifeste")
    else:
        p5_details.append("Manifeste llms.txt absent")
        p5_details.append("Configuration MCP manquante")
    p5_score = max(5, min(100, p5_score))

    # Score Global Composite (20% + 25% + 20% + 20% + 15% = 100%)
    total = int(
        (p1_score * 0.20)
        + (schema_res["score"] * 0.25)
        + (semantic_res["score"] * 0.20)
        + (p4_score * 0.20)
        + (p5_score * 0.15)
    )
    total = max(5, min(100, total))

    # Broken Items (Pain points for Cold Email)
    broken_items: list[BrokenItem] = []
    if p1_score < 75:
        broken_items.append(
            BrokenItem(
                title="Blocage des crawlers IA dans robots.txt ou WAF",
                impact="GPTBot (ChatGPT) et ClaudeBot sont refoulés lors de l'indexation de vos fiches.",
                severity="critical",
            )
        )
    if not schema_res.get("has_product"):
        broken_items.append(
            BrokenItem(
                title="Absence totale de balisage Schema.org Product",
                impact="L'IA ne peut pas extraire le nom, le stock ni le SKU de vos produits.",
                severity="critical",
            )
        )
    if not prod_data.has_shipping:
        broken_items.append(
            BrokenItem(
                title="Balise shippingDetails manquante",
                impact="L'agent d'achat IA ignore les frais de port et refuse de recommander le produit.",
                severity="critical" if total < 50 else "warning",
            )
        )
    if not prod_data.has_return:
        broken_items.append(
            BrokenItem(
                title="Politique de retour (hasMerchantReturnPolicy) absente",
                impact="Les acheteurs IA hésitent faute de garantie claire sur les retours.",
                severity="warning",
            )
        )
    if p5_score < 50:
        broken_items.append(
            BrokenItem(
                title="Absence du protocole llms.txt & configuration MCP",
                impact="Catalogue invisible pour les moteurs agentiques autonomes.",
                severity="warning",
            )
        )

    status = "Excellente visibilité IA" if total >= 75 else ("Fragilité IA" if total >= 40 else "Invisibilité IA Critique")
    badge = "bg-emerald-500/10 text-emerald-500" if total >= 75 else ("bg-amber-500/10 text-amber-500" if total >= 40 else "bg-rose-500/10 text-rose-500")

    pillars = {
        "crawl": PillarScore(
            score=p1_score, weight="20%", status="OK" if p1_score >= 70 else "Alerte", label="Crawl & Bots IA", details=p1_details
        ),
        "schema": PillarScore(
            score=schema_res["score"], weight="25%", status="OK" if schema_res["score"] >= 70 else "Alerte", label="Données Schema.org", details=schema_res["details"]
        ),
        "semantic": PillarScore(
            score=semantic_res["score"], weight="20%", status="OK" if semantic_res["score"] >= 70 else "Alerte", label="Pureté Sémantique", details=semantic_res["details"]
        ),
        "simulator": PillarScore(
            score=p4_score, weight="20%", status="OK" if p4_score >= 70 else "Alerte", label="Simulateur Achat IA", details=p4_details
        ),
        "protocols": PillarScore(
            score=p5_score, weight="15%", status="OK" if p5_score >= 70 else "Alerte", label="Protocoles llms.txt/MCP", details=p5_details
        ),
    }

    autofix = _generate_auto_fix(domain, prod_data)

    return AuditResult(
        domain=domain,
        name=prod_data.name or domain,
        score=total,
        status=status,
        statusLabel=status,
        statusBadgeClass=badge,
        summary=f"Score de visibilité IA de {total}/100 sur {domain}.",
        pillars=pillars,
        productData=prod_data,
        brokenItems=broken_items,
        autoFix=autofix,
        fixedJsonLd=autofix.get("schemaJson", ""),
        isWafBlocked=is_waf_blocked,
    )
