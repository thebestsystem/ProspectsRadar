"""Unit tests for 5-pillar scanner, leads pipeline, and pitch generation."""

import pytest

from app.repo.crawler import normalize_scan_url, parse_robots_txt
from app.repo.leads_repo import export_leads_to_csv, list_leads
from app.repo.parser_schema import analyze_schema
from app.service.pitch_writer import generate_cold_pitch
from app.types.scanner import BrokenItem, DecisionMaker


def test_normalize_scan_url():
    """Verify URL normalization adds scheme and rejects invalid domains."""
    assert normalize_scan_url("respire.co") == "https://respire.co"
    assert normalize_scan_url("https://horace.co/fr") == "https://horace.co/fr"

    with pytest.raises(ValueError):
        normalize_scan_url("")

    with pytest.raises(ValueError):
        normalize_scan_url("invalid host with spaces")


def test_parse_robots_txt_detects_ai_bots():
    """Verify parser catches restrictions specifically targeting GPTBot and ClaudeBot."""
    sample_robots = """
    User-agent: *
    Disallow: /checkout

    User-agent: GPTBot
    Disallow: /

    User-agent: ClaudeBot
    Disallow: /
    """
    disallowed, is_global = parse_robots_txt(sample_robots)
    assert not is_global
    assert "gptbot" in disallowed
    assert "claudebot" in disallowed


def test_analyze_schema_with_offer():
    """Verify Schema.org Product and Offer analysis scores attributes properly."""
    sample_json_ld = [{
        "@type": "Product",
        "name": "Crème Hydratante Bio",
        "sku": "CREM-01",
        "offers": {
            "@type": "Offer",
            "price": "19.90",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock",
            "shippingDetails": {"@type": "OfferShippingDetails"},
            "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy"},
        }
    }]
    res = analyze_schema(sample_json_ld)
    assert res["score"] == 100
    assert res["product_data"]["name"] == "Crème Hydratante Bio"
    assert res["product_data"]["price"] == "19.90"
    assert res["product_data"]["has_shipping"] is True


def test_generate_cold_pitch():
    """Verify cold pitch cites exact score, domain, and flaw details."""
    dm = DecisionMaker(name="Alexandre Moreau", title="Fondateur", email="alex@shop.fr")
    broken = [
        BrokenItem(title="Balise shippingDetails manquante", impact="L'IA ignore les frais de port"),
        BrokenItem(title="Protocole llms.txt absent", impact="Catalogue invisible"),
    ]
    pitch = generate_cold_pitch(
        domain="shop.fr",
        company_name="Shop",
        score=27,
        broken_items=broken,
        failing_pillars=["Données Schema.org", "Protocoles llms.txt"],
        dm=dm,
    )
    assert "score : 27/100" in pitch
    assert "Bonjour Alexandre" in pitch
    assert "Balise shippingDetails manquante" in pitch
    assert "shop.fr" in pitch


def test_leads_repo_and_csv_export():
    """Verify leads are listed and exportable to CSV with all required columns."""
    leads = list_leads()
    assert len(leads) >= 1

    csv_data = export_leads_to_csv()
    assert "Website,Company_Name,Vertical,AI_Score" in csv_data
    assert leads[0].domain in csv_data
