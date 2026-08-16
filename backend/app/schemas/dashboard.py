from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_invoices: int
    failed_invoices: int
    passed_invoices: int
    total_overcharge: float
    average_overcharge: float


class BreakdownItem(BaseModel):
    name: str
    count: int
    amount: float = 0.0


class DashboardBreakdown(BaseModel):
    errors: list[BreakdownItem]
    severity: list[BreakdownItem]


class RecentAudit(BaseModel):
    invoice_id: str
    shipment_id: str
    load_id: str
    status: str
    severity: str
    overcharge_amount: float


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    breakdown: DashboardBreakdown
    recent_audits: list[RecentAudit]