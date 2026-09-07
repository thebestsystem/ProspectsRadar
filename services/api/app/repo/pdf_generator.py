"""
==========================================================================
PDF generator module (ReportLab) for ProspectsRadar
==========================================================================
Rendus ReportLab des rapports d'audit de visibilité IA e-commerce (white-label).
"""

import io
from datetime import datetime
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    REPORTLAB_AVAILABLE = False

from xml.sax.saxutils import escape as _sax_escape


def _escape_xml(val: Any) -> str:
    """Échappe le texte dynamique pour éviter les erreurs de parsing XML dans ReportLab."""
    if val is None:
        return ""
    return _sax_escape(str(val))


def generate_pdf_report(audit_data: dict[str, Any], email: str | None = None) -> bytes:
    """Génère le PDF d'audit vectoriel (bytes). Lève RuntimeError si ReportLab absent."""
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab n'est pas installé sur le serveur.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    story = []

    c_cyan = colors.HexColor("#06b6d4")
    c_emerald = colors.HexColor("#10b981")
    c_rose = colors.HexColor("#f43f5e")
    c_amber = colors.HexColor("#f59e0b")
    c_text_muted = colors.HexColor("#64748b")

    brand_style = ParagraphStyle(
        "BrandStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=c_cyan,
        fontName="Helvetica-Bold",
    )
    title_style = ParagraphStyle(
        "MainTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    # 1. Header Banner
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
    header_data = [
        [
            Paragraph("<b>ProspectsRadar</b> • Rapport d'Audit White-Label 2026", brand_style),
            Paragraph(f"Date d'analyse : <b>{date_str}</b>", normal_style),
        ]
    ]
    t_header = Table(header_data, colWidths=[360, 180])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_cyan, spaceBefore=0, spaceAfter=15))

    # 2. Executive Summary Block
    name = audit_data.get("name") or "Boutique E-commerce"
    domain = audit_data.get("domain") or "https://example.com"
    score = audit_data.get("score", 50)
    status_label = audit_data.get("statusLabel") or ("Visibilité IA Optimale" if score >= 80 else ("Friction IA" if score >= 50 else "Invisibilité IA Critique"))
    summary_text = audit_data.get("summary") or "Évaluation de la préparation de la boutique pour les agents d'achat IA."

    score_color = c_emerald if score >= 80 else (c_amber if score >= 50 else c_rose)
    score_color_hex = f"#{score_color.hexval()[2:]}"

    safe_name = _escape_xml(name)
    safe_domain = _escape_xml(domain)
    safe_status_label = _escape_xml(status_label)
    safe_summary = _escape_xml(summary_text)
    safe_email = _escape_xml(email) if email else "Confidentiel"

    story.append(Paragraph(f"Audit Technique : {safe_name}", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"URL cible : <u>{safe_domain}</u>", normal_style))
    story.append(Spacer(1, 12))

    summary_box_data = [
        [
            Paragraph(f"<font size=28 color='{score_color_hex}'><b>{score}</b></font><font size=14 color='#64748b'>/100</font><br/><br/><b>Statut :</b> {safe_status_label}", normal_style),
            Paragraph(f"<b>Synthèse de l'Audit :</b><br/>{safe_summary}<br/><br/><i>Client destinataire : {safe_email}</i>", normal_style),
        ]
    ]
    t_summary = Table(summary_box_data, colWidths=[160, 380])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # 3. Tableau des 5 Piliers
    story.append(Paragraph("Détail des 5 Piliers d'Évaluation Agentique", section_style))
    story.append(Spacer(1, 6))

    pillars = audit_data.get("pillars", {})
    p_crawl = pillars.get("crawl", {})
    p_schema = pillars.get("schema", {})
    p_tokens = pillars.get("tokens") or pillars.get("semantic", {})
    p_sim = pillars.get("simulator", {})
    p_proto = pillars.get("proto") or pillars.get("protocols", {})

    pillars_rows = [
        [Paragraph("<b>Pilier</b>", normal_style), Paragraph("<b>Pondération</b>", normal_style), Paragraph("<b>Score</b>", normal_style), Paragraph("<b>Statut Technique</b>", normal_style)],
        [Paragraph("1. Crawl & Bot Access (robots.txt / WAF)", normal_style), Paragraph("20%", normal_style), Paragraph(f"<b>{_escape_xml(p_crawl.get('score', '--'))}/100</b>", normal_style), Paragraph(_escape_xml(p_crawl.get('status', '--')), normal_style)],
        [Paragraph("2. Schema.org & JSON-LD Déterministe", normal_style), Paragraph("25%", normal_style), Paragraph(f"<b>{_escape_xml(p_schema.get('score', '--'))}/100</b>", normal_style), Paragraph(_escape_xml(p_schema.get('status', '--')), normal_style)],
        [Paragraph("3. Pureté Sémantique & Économie de Tokens", normal_style), Paragraph("20%", normal_style), Paragraph(f"<b>{_escape_xml(p_tokens.get('score', '--'))}/100</b>", normal_style), Paragraph(_escape_xml(p_tokens.get('status', '--')), normal_style)],
        [Paragraph("4. AI Buyer Simulator (Fallback DOM)", normal_style), Paragraph("20%", normal_style), Paragraph(f"<b>{_escape_xml(p_sim.get('score', '--'))}/100</b>", normal_style), Paragraph(_escape_xml(p_sim.get('status', '--')), normal_style)],
        [Paragraph("5. Protocoles Agentiques (llms.txt / MCP)", normal_style), Paragraph("15%", normal_style), Paragraph(f"<b>{_escape_xml(p_proto.get('score', '--'))}/100</b>", normal_style), Paragraph(_escape_xml(p_proto.get('status', '--')), normal_style)],
    ]

    t_pillars = Table(pillars_rows, colWidths=[220, 70, 70, 180])
    t_pillars.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_pillars)
    story.append(Spacer(1, 15))

    # 4. Éléments cassés identifiés
    broken_items = audit_data.get("brokenItems", [])
    if broken_items:
        story.append(Paragraph("Failles Techniques Identifiées (Broken Items)", section_style))
        story.append(Spacer(1, 6))
        broken_rows = [[Paragraph("<b>Faiblesse détectée</b>", normal_style), Paragraph("<b>Impact IA</b>", normal_style)]]
        for b in broken_items[:6]:
            broken_rows.append([
                Paragraph(f"• {_escape_xml(b.get('title', ''))}", normal_style),
                Paragraph(_escape_xml(b.get("impact", "")), normal_style),
            ])
        t_broken = Table(broken_rows, colWidths=[240, 300])
        t_broken.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t_broken)
        story.append(Spacer(1, 12))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_text_muted, spaceBefore=10, spaceAfter=8))
    story.append(Paragraph(
        "Rapport certifié édité par la plateforme ProspectsRadar. Les standards d'audit suivent les spécifications W3C Schema.org 2026 et les protocoles LLMs.txt & Model Context Protocol (MCP).",
        ParagraphStyle("Foot", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=c_text_muted),
    ))

    doc.build(story)
    return buffer.getvalue()
