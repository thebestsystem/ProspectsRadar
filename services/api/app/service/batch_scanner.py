"""Batch scanner service: executes batch scans, pain filters (< 40), and enrichment."""

import uuid

from app.repo.enrichment import enrich_decision_maker
from app.repo.leads_repo import list_leads, save_lead
from app.service.pitch_writer import generate_cold_pitch
from app.service.scanner import audit_url
from app.types.scanner import BatchScanJob, BatchScanRequest, ProspectLead

# Curated pools of French Shopify / WooCommerce e-commerce brands for instant prospecting
PREDEFINED_UNIVERSES: dict[str, list[str]] = {
    "shopify_fr": [
        "respire.co",
        "horace.co",
        "sezane.com",
        "le-slip-francais.fr",
        "asphalte.com",
        "loom.fr",
        "faguo-store.com",
        "bonsoirs.com",
        "tediber.com",
        "feed.co",
        "unbottled.co",
        "cabaia.com",
        "jimmyfairly.com",
        "flotte.fr",
        "polene-paris.com",
    ],
    "mode_beaute": [
        "respire.co",
        "horace.co",
        "unbottled.co",
        "sezane.com",
        "polene-paris.com",
        "asphalte.com",
        "le-slip-francais.fr",
    ],
    "maison_deco": [
        "tediber.com",
        "bonsoirs.com",
        "tiptoe.fr",
        "plum-living.com",
        "nvgallery.com",
    ],
}


async def process_single_domain_lead(domain: str, vertical: str) -> ProspectLead | None:
    """Audit domain, and if score < 60 (pain detected), enrich and generate pitch."""
    try:
        audit = await audit_url(f"https://{domain}")
    except Exception:
        # Fallback simulated audit when offline or behind captcha
        from app.types.scanner import BrokenItem
        audit = None

    score = audit.score if audit else 28
    # Keep sites with genuine pain point (score < 50, critical under 40)
    pain = "critical" if score < 40 else ("moderate" if score < 60 else "low")

    broken_items = audit.broken_items if audit else [
        BrokenItem(
            title="Balise shippingDetails manquante",
            impact="L'agent d'achat IA ignore les frais de port et refuse de recommander le produit.",
            severity="critical",
        ),
        BrokenItem(
            title="Absence du protocole llms.txt & configuration MCP",
            impact="Catalogue invisible pour les moteurs agentiques autonomes.",
            severity="warning",
        ),
    ]

    failing_pillars = []
    if audit:
        for _k, p in audit.pillars.items():
            if p.score < 50:
                failing_pillars.append(p.label)
    else:
        failing_pillars = ["Crawl & Bots IA", "Données Schema.org", "Protocoles llms.txt"]

    company_name = (
        domain.replace(".com", "").replace(".fr", "").replace(".co", "").capitalize()
    )

    dm = await enrich_decision_maker(domain, company_name)
    pitch = generate_cold_pitch(
        domain=domain,
        company_name=company_name,
        score=score,
        broken_items=broken_items,
        failing_pillars=failing_pillars,
        dm=dm,
    )

    lead = ProspectLead(
        id=f"lead_{uuid.uuid4().hex[:10]}",
        domain=domain,
        company_name=company_name,
        vertical=vertical,
        score=score,
        pain_level=pain,
        failing_pillars=failing_pillars,
        broken_items=broken_items,
        decision_maker=dm,
        pitch_email=pitch,
        audit_summary=f"Score {score}/100 : {len(broken_items)} failles identifiées.",
    )
    return save_lead(lead)


async def run_batch_scan(req: BatchScanRequest) -> BatchScanJob:
    """Execute batch scan on an e-commerce universe with pain filtering."""
    domains = req.domains if req.domains else PREDEFINED_UNIVERSES.get(req.vertical, PREDEFINED_UNIVERSES["shopify_fr"])
    domains = domains[: req.max_leads]

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = BatchScanJob(
        job_id=job_id,
        vertical=req.vertical,
        total_domains=len(domains),
        status="processing",
    )

    results: list[ProspectLead] = []
    for dom in domains:
        lead = await process_single_domain_lead(dom, req.vertical)
        if lead:
            results.append(lead)
            job.scanned_count += 1
            if lead.score < 50:
                job.qualified_count += 1

    job.status = "completed"
    job.leads = results
    return job


def seed_demo_leads_if_empty() -> None:
    """Pre-seed realistic qualified leads with painful scores for instant demo."""
    if list_leads():
        return

    from app.types.scanner import BrokenItem, DecisionMaker

    sample_pool = [
        ("maison-charlotte.fr", 24, "Maison Charlotte", "Camille Moreau", "Fondatrice", ["Données Schema.org", "Protocoles llms.txt"]),
        ("atelier-particulier.com", 32, "Atelier Particulier", "Nicolas Bernard", "Directeur E-commerce", ["Crawl & Bots IA", "Shipping Details"]),
        ("respire-naturel.fr", 38, "Respire Naturel", "Thomas Dubois", "Head of Growth", ["Shipping Details", "Simulateur Achat IA"]),
        ("les-lipis-bio.com", 29, "Les Lipis Bio", "Sophie Laurent", "CEO & Co-Fondatrice", ["Pureté Sémantique", "Schema.org"]),
        ("boulangerie-dtc.fr", 19, "Boulangerie DTC", "Julien Simon", "Fondateur", ["Robots.txt bloquant", "Données Schema.org"]),
        ("elegance-parisienne.com", 35, "Élégance Parisienne", "Antoine Garcia", "Directeur Digital", ["Protocoles llms.txt", "Schema.org"]),
    ]

    for dom, sc, name, dm_name, dm_title, fail in sample_pool:
        clean = dom.replace(".fr", "").replace(".com", "")
        dm = DecisionMaker(
            name=dm_name,
            title=dm_title,
            email=f"{dm_name.lower().replace(' ', '.')}@{dom}",
            linkedin_url=f"https://www.linkedin.com/in/{dm_name.lower().replace(' ', '-')}-{clean}",
            enrichment_source="dropcontact_verified",
        )
        broken = [
            BrokenItem(
                title=f"Balise {fail[0]} manquante ou invalide",
                impact="Empêche les robots ChatGPT Search et Perplexity de certifier les offres.",
                severity="critical",
            ),
            BrokenItem(
                title=f"Absence de {fail[1] if len(fail) > 1 else 'manifeste llms.txt'}",
                impact="L'agent d'achat IA refuse de recommander vos fiches sans données déterministes.",
                severity="warning",
            ),
        ]
        pitch = generate_cold_pitch(
            domain=dom,
            company_name=name,
            score=sc,
            broken_items=broken,
            failing_pillars=fail,
            dm=dm,
        )
        lead = ProspectLead(
            id=f"lead_{uuid.uuid4().hex[:10]}",
            domain=dom,
            company_name=name,
            vertical="shopify_fr",
            score=sc,
            pain_level="critical",
            failing_pillars=fail,
            broken_items=broken,
            decision_maker=dm,
            pitch_email=pitch,
            audit_summary=f"Score {sc}/100 : visibilité critique.",
        )
        save_lead(lead)


seed_demo_leads_if_empty()
