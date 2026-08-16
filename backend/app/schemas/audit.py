from typing import Any

from pydantic import BaseModel


class FinancialSummary(BaseModel):
    billed_amount: float
    expected_amount: float
    overcharge_amount: float


class Finding(BaseModel):
    type: str
    title: str
    billed_amount: float
    expected_amount: float
    variance: float
    actual_distance_miles: float | None = None
    contract_rate_per_mile: float | None = None
    calculation: str | None = None
    explanation: str


class CheckResult(BaseModel):
    status: str
    variance: float


class Evidence(BaseModel):
    contract_source: str | None = None
    shipment_source: str | None = None
    load_source: str | None = None
    delivery_source: str | None = None


class MLResult(BaseModel):
    risk: str | None = None
    anomaly_score: float | None = None


class AuditResponse(BaseModel):
    invoice_id: str
    shipment_id: str
    load_id: str
    contract_id: str

    status: str
    severity: str

    financial_summary: FinancialSummary

    findings: list[Finding]

    checks: dict[str, Any]

    evidence: Evidence

    ml: MLResult

    matching: dict[str, Any]

    invoice: dict[str, Any]