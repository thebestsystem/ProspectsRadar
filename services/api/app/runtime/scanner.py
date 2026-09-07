"""FastAPI router for AI visibility scanning, qualified leads, and exports."""

from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response

from app.repo.leads_repo import (
    export_leads_to_csv,
    generate_lead_audit_pdf,
    get_lead_by_id,
    list_leads,
)
from app.service.batch_scanner import run_batch_scan
from app.service.scanner import audit_url
from app.types.scanner import AuditResult, BatchScanJob, BatchScanRequest, ProspectLead, ScanRequest

router = APIRouter(tags=["scanner", "leads"])


@router.post("/scan", response_model=AuditResult)
async def scan_single_target(req: ScanRequest) -> AuditResult:
    """Run an instant 5-pillar audit on a single e-commerce URL."""
    try:
        return await audit_url(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec du scan : {e}") from e


@router.post("/leads/batch", response_model=BatchScanJob)
async def launch_batch_scan(req: BatchScanRequest) -> BatchScanJob:
    """Launch batch scan on a vertical or custom domain list, filtering pain points."""
    try:
        return await run_batch_scan(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur batch : {e}") from e


@router.get("/leads", response_model=list[ProspectLead])
async def get_qualified_leads(
    vertical: str = Query("all"),
    min_score: int | None = Query(None),
    max_score: int | None = Query(None),
) -> list[ProspectLead]:
    """Retrieve pre-qualified leads with failing pillars and customized cold pitch."""
    return list_leads(vertical=vertical, min_score=min_score, max_score=max_score)


@router.get("/leads/stats")
async def get_leads_dashboard_stats() -> dict[str, Any]:
    """Aggregate stats for agency dashboard: qualified count, pain rates, top flaws."""
    leads = list_leads()
    total = len(leads)
    critical_pain = sum(1 for lead in leads if lead.score < 40) if total else 0
    avg_score = int(sum(lead.score for lead in leads) / total) if total else 0

    pillar_counts: Counter[str] = Counter()
    for lead in leads:
        for p in lead.failing_pillars:
            pillar_counts[p] += 1

    return {
        "total_leads": total,
        "critical_pain_count": critical_pain,
        "critical_pain_rate": int((critical_pain / total) * 100) if total else 0,
        "average_score": avg_score,
        "top_failing_pillars": dict(pillar_counts.most_common(5)),
    }


@router.get("/leads/export.csv")
async def export_leads_csv(vertical: str = Query("all")) -> Response:
    """Download pre-qualified leads as formatted CSV for Instantly/Smartlead/CRM."""
    csv_content = export_leads_to_csv(vertical=vertical)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=prospects_radar_{vertical}.csv",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/leads/{lead_id}/pdf")
async def download_lead_audit_pdf(lead_id: str) -> Response:
    """Generate and stream white-label PDF audit report for cold email attachment."""
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead introuvable")
    try:
        pdf_bytes = generate_lead_audit_pdf(lead)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=audit_{lead.domain}.pdf",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur PDF : {e}") from e
