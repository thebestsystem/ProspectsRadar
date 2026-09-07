"""Types and schemas for the AI visibility 5-pillar scanner and lead pipeline."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class PillarScore(BaseModel):
    score: int
    max_score: int = Field(default=100, alias="max")
    weight: str
    status: str
    label: str
    details: list[str] = []

    model_config = {"populate_by_name": True}


class BrokenItem(BaseModel):
    title: str
    impact: str
    severity: str = "critical"


class ProductData(BaseModel):
    name: str | None = None
    sku: str | None = None
    image: str | None = None
    price: str = "Inconnu"
    currency: str = "EUR"
    has_shipping: bool = False
    has_return: bool = False
    has_stock: bool = False
    description: str = ""
    price_source: str | None = None
    stock_source: str | None = None
    price_detail: str | None = None
    is_product_page: bool = True


class AuditResult(BaseModel):
    domain: str
    name: str
    image: str | None = None
    score: int
    status: str
    status_label: str = Field(default="", alias="statusLabel")
    status_badge_class: str = Field(default="", alias="statusBadgeClass")
    summary: str = ""
    pillars: dict[str, PillarScore] = {}
    ai_view: dict[str, str] = Field(default_factory=dict, alias="aiView")
    auto_fix: dict[str, str] = Field(default_factory=dict, alias="autoFix")
    product_data: ProductData = Field(default_factory=ProductData, alias="productData")
    broken_items: list[BrokenItem] = Field(default_factory=list, alias="brokenItems")
    raw_json_ld: str = Field(default="", alias="rawJsonLd")
    fixed_json_ld: str = Field(default="", alias="fixedJsonLd")
    is_waf_blocked: bool = Field(default=False, alias="isWafBlocked")
    waf_details: dict[str, str] | None = Field(default=None, alias="wafDetails")
    audit_type: str = Field(default="STANDARD", alias="auditType")
    gemini_live: bool = Field(default=False, alias="geminiLive")
    is_product_page: bool = Field(default=True, alias="isProductPage")

    model_config = {"populate_by_name": True}


class ScanRequest(BaseModel):
    url: str


class DecisionMaker(BaseModel):
    name: str
    title: str
    email: str
    linkedin_url: str | None = None
    enrichment_source: str = "dropcontact"


class ProspectLead(BaseModel):
    id: str
    domain: str
    company_name: str
    vertical: str = "shopify_fr"
    score: int
    pain_level: str = "critical"  # critical (< 40), moderate (40-60), low (> 60)
    status: str = "new"  # new, contacted, interested, converted, archived
    failing_pillars: list[str] = []
    broken_items: list[BrokenItem] = []
    decision_maker: DecisionMaker
    pitch_email: str
    audit_summary: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


class BatchScanRequest(BaseModel):
    vertical: str = "shopify_fr"
    domains: list[str] = []
    max_leads: int = 50


class BatchScanJob(BaseModel):
    job_id: str
    vertical: str
    total_domains: int
    scanned_count: int = 0
    qualified_count: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    leads: list[ProspectLead] = []
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
