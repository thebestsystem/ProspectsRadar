"""Schema.org JSON-LD extractor and structured data analyzer."""

import json
import re
from typing import Any

from bs4 import BeautifulSoup


def clean_json_ld_text(text: str) -> str:
    """Strip CDATA and HTML comment tags frequently wrapping JSON-LD."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"^\s*//\s*<!\[CDATA\[", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*<!\[CDATA\[", "", t, flags=re.IGNORECASE)
    t = re.sub(r"//\s*\]\]>\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\]\]>\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*<!--", "", t)
    t = re.sub(r"-->\s*$", "", t)
    return t.strip()


def extract_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract all valid JSON-LD objects from script tags in HTML."""
    json_ld_list: list[dict[str, Any]] = []
    scripts = soup.find_all("script", type=lambda t: t and "ld+json" in t.lower())
    for s in scripts:
        raw = clean_json_ld_text(s.get_text())
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                json_ld_list.extend(data)
            elif isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list):
                    json_ld_list.extend(data["@graph"])
                else:
                    json_ld_list.append(data)
        except Exception:
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
            if m:
                try:
                    data = json.loads(m.group(1))
                    if isinstance(data, list):
                        json_ld_list.extend(data)
                    elif isinstance(data, dict):
                        if "@graph" in data and isinstance(data["@graph"], list):
                            json_ld_list.extend(data["@graph"])
                        else:
                            json_ld_list.append(data)
                except Exception:
                    pass
    return json_ld_list


def analyze_schema(json_ld_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Inspect JSON-LD items for Schema.org Product and Offer standards."""
    product_obj = None
    for item in json_ld_list:
        if isinstance(item, dict) and "Product" in str(item.get("@type", "")):
            product_obj = item
            break

    if not product_obj:
        return {
            "score": 25,
            "status": "Aucun schéma Product JSON-LD trouvé",
            "has_product": False,
            "details": [
                "Balise @type: Product absente du code source",
                "L'IA ne peut pas identifier les attributs certifiés de l'offre",
            ],
            "product_data": {
                "name": None,
                "sku": None,
                "image": None,
                "price": "Inconnu",
                "currency": "EUR",
                "has_shipping": False,
                "has_return": False,
                "has_stock": False,
                "description": "",
                "price_source": None,
                "stock_source": None,
            },
        }

    score = 40
    details = ["Schéma @type: Product détecté (+40 pts)"]
    prod_name = product_obj.get("name", "Produit sans titre")
    prod_sku = (
        product_obj.get("sku")
        or product_obj.get("gtin13")
        or product_obj.get("gtin")
    )
    prod_desc = product_obj.get("description", "")

    if prod_sku:
        score += 10
        details.append(f"Identifiant unique machine présent : SKU/GTIN ({prod_sku})")
    else:
        details.append("Identifiant unique SKU/GTIN manquant")

    offers = product_obj.get("offers", {})
    if isinstance(offers, list) and len(offers) > 0:
        offers = offers[0]

    has_price = False
    price_val = "Inconnu"
    currency = "EUR"
    has_shipping = False
    has_return = False
    has_stock = False

    if isinstance(offers, dict):
        raw_price = offers.get("price")
        if raw_price is not None and str(raw_price).strip() not in (
            "", "None", "null", "undefined"
        ):
            has_price = True
            price_val = str(raw_price).strip()
            raw_curr = offers.get("priceCurrency")
            currency = (
                str(raw_curr).strip().upper()
                if raw_curr and str(raw_curr).strip() not in ("", "None", "null")
                else "EUR"
            )
            score += 20
            details.append(f"Prix explicite trouvé : {price_val} {currency}")

        if "availability" in offers:
            has_stock = True
            score += 10
            details.append("Disponibilité en stock structurée")

        if "shippingDetails" in offers or "shippingRate" in offers:
            has_shipping = True
            score += 10
            details.append("Frais & délais de livraison (shippingDetails) présents")
        else:
            details.append(
                "shippingDetails absent : L'IA ne peut pas calculer les frais de port"
            )

        if "hasMerchantReturnPolicy" in offers:
            has_return = True
            score += 10
            details.append("Politique de retour (hasMerchantReturnPolicy) conforme")
        else:
            details.append("hasMerchantReturnPolicy absent : Risque d'hésitation pour l'agent IA")

    score = min(100, score)
    return {
        "score": score,
        "status": "Conforme" if score >= 80 else ("Partiel" if score >= 50 else "Critique"),
        "has_product": True,
        "details": details,
        "product_data": {
            "name": prod_name,
            "sku": prod_sku,
            "price": price_val,
            "currency": currency,
            "has_shipping": has_shipping,
            "has_return": has_return,
            "has_stock": has_stock,
            "description": prod_desc[:200] if prod_desc else "",
            "price_source": "schema" if has_price else None,
            "stock_source": "schema" if has_stock else None,
        },
    }
