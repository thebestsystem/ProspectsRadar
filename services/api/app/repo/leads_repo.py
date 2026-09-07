"""Leads repository: storage, CSV export, and PDF generation."""

import csv
import io
import json
import os

from app.types.scanner import ProspectLead

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LEADS_FILE = os.path.join(DATA_DIR, "prospect_leads.json")

# In-memory store initialized with any persisted leads
_leads_store: dict[str, ProspectLead] = {}


def _load_persisted_leads() -> None:
    global _leads_store
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, encoding="utf-8") as f:
                raw = json.load(f)
                for item in raw:
                    lead = ProspectLead(**item)
                    _leads_store[lead.id] = lead
        except Exception:
            pass


_load_persisted_leads()


def _save_persisted_leads() -> None:
    try:
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump([lead.model_dump() for lead in _leads_store.values()], f, indent=2)
    except Exception:
        pass


def save_lead(lead: ProspectLead) -> ProspectLead:
    """Save or update a prospect lead in memory and persistent storage."""
    _leads_store[lead.id] = lead
    _save_persisted_leads()
    return lead


def list_leads(vertical: str | None = None, min_score: int | None = None, max_score: int | None = None) -> list[ProspectLead]:
    """List stored qualified leads with optional score and vertical filters."""
    results = list(_leads_store.values())
    if vertical and vertical != "all":
        results = [lead_item for lead_item in results if lead_item.vertical.lower() == vertical.lower()]
    if min_score is not None:
        results = [lead_item for lead_item in results if lead_item.score >= min_score]
    if max_score is not None:
        results = [lead_item for lead_item in results if lead_item.score <= max_score]
    return sorted(results, key=lambda lead_item: lead_item.score)


def get_lead_by_id(lead_id: str) -> ProspectLead | None:
    """Retrieve a single lead by its unique id."""
    return _leads_store.get(lead_id)


def export_leads_to_csv(vertical: str | None = None) -> str:
    """Export qualified leads in standard CSV format for Instantly/Smartlead/HubSpot."""
    leads = list_leads(vertical)
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        "Website",
        "Company_Name",
        "Vertical",
        "AI_Score",
        "Pain_Level",
        "Decision_Maker_Name",
        "Title",
        "Email",
        "LinkedIn",
        "Cold_Pitch",
        "Failing_Pillars",
        "Created_At",
    ])

    for lead in leads:
        writer.writerow([
            lead.domain,
            lead.company_name,
            lead.vertical,
            lead.score,
            lead.pain_level,
            lead.decision_maker.name,
            lead.decision_maker.title,
            lead.decision_maker.email,
            lead.decision_maker.linkedin_url or "",
            lead.pitch_email,
            "; ".join(lead.failing_pillars),
            lead.created_at,
        ])

    return output.getvalue()


def generate_lead_audit_pdf(lead: ProspectLead) -> bytes:
    """Generate professional PDF audit report for lead pitch attachment."""
    from app.repo.pdf_generator import generate_pdf_report

    audit_dict = {
        "domain": lead.domain,
        "name": lead.company_name,
        "score": lead.score,
        "statusLabel": "Invisibilité IA Critique" if lead.score < 40 else "Fragilité IA",
        "summary": lead.audit_summary or f"Audit visibilité IA de {lead.domain}",
        "brokenItems": [{"title": b.title, "impact": b.impact} for b in lead.broken_items],
        "pillars": {
            "crawl": {"score": 30, "status": "Critique", "label": "Crawl & Bots IA"},
            "schema": {"score": 25, "status": "Critique", "label": "Données Schema.org"},
            "semantic": {"score": 40, "status": "Alerte", "label": "Pureté Sémantique"},
            "simulator": {"score": 30, "status": "Alerte", "label": "Simulateur Achat IA"},
            "protocols": {"score": 10, "status": "Critique", "label": "Protocoles llms.txt"},
        },
        "productData": {
            "name": lead.company_name,
            "sku": "PROD-01",
            "price": "29.90",
            "currency": "EUR",
            "has_shipping": False,
            "has_return": False,
            "has_stock": True,
        },
    }
    return generate_pdf_report(audit_dict, email=lead.decision_maker.email)
