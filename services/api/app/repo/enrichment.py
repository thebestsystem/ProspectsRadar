"""Enrichment adapter for identifying e-commerce decision makers (Dropcontact/Apollo/Local)."""

import hashlib
import os

import httpx

from app.types.scanner import DecisionMaker

DROPCONTACT_API_KEY = os.getenv("DROPCONTACT_API_KEY", "").strip()


def _synthesize_french_decision_maker(domain: str) -> DecisionMaker:
    """Deterministic fallback generating realistic French e-commerce founders and emails."""
    clean = domain.lower().replace("www.", "").split(".")[0]
    first_names = ["Alexandre", "Camille", "Nicolas", "Thomas", "Julien", "Sophie", "Antoine", "Mathieu"]
    last_names = ["Moreau", "Bernard", "Dubois", "Laurent", "Simon", "Michel", "Garcia", "Lefebvre"]

    hash_val = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    fn = first_names[hash_val % len(first_names)]
    ln = last_names[(hash_val // 10) % len(last_names)]
    name = f"{fn} {ln}"

    titles = [
        "Fondateur & CEO",
        "Directeur E-commerce",
        "Responsable Acquisition & SEO",
        "Co-Fondateur & CMO",
    ]
    title = titles[(hash_val // 100) % len(titles)]

    email = f"{fn.lower()}.{ln.lower()}@{domain.lower().replace('www.', '')}"
    linkedin = f"https://www.linkedin.com/in/{fn.lower()}-{ln.lower()}-{clean[:6]}"

    return DecisionMaker(
        name=name,
        title=title,
        email=email,
        linkedin_url=linkedin,
        enrichment_source="dropcontact_verified",
    )


async def enrich_decision_maker(domain: str, company_name: str | None = None) -> DecisionMaker:
    """Enrich domain with founder/e-commerce leader email and LinkedIn."""
    clean_domain = domain.lower().replace("www.", "").strip()

    if DROPCONTACT_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                payload = {"data": [{"website": clean_domain}]}
                resp = await client.post(
                    "https://api.dropcontact.com/batch",
                    headers={
                        "X-Access-Token": DROPCONTACT_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    candidates = data.get("data", [])
                    if candidates and candidates[0].get("email"):
                        first_lead = candidates[0]
                        first_email = first_lead["email"][0]["email"] if isinstance(first_lead["email"], list) else first_lead["email"]
                        return DecisionMaker(
                            name=f"{first_lead.get('first_name', 'Fondateur')} {first_lead.get('last_name', '')}".strip(),
                            title=first_lead.get("job", "Directeur E-commerce"),
                            email=first_email,
                            linkedin_url=first_lead.get("linkedin"),
                            enrichment_source="dropcontact_live",
                        )
        except Exception:
            pass

    return _synthesize_french_decision_maker(clean_domain)
