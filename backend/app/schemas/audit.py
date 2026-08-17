from typing import Any

from pydantic import BaseModel, Field


class FinancialSummary(BaseModel):
    billed_amount: float = 0.0
    expected_amount: float = 0.0
    overcharge_amount: float = 0.0


class Finding(BaseModel):
    type: str
    title: str

    billed_amount: float = 0.0
    expected_amount: float = 0.0
    variance: float = 0.0

    actual_distance_miles: float | None = None
    contract_rate_per_mile: float | None = None

    calculation: str | None = None

    explanation: str


class CheckResult(BaseModel):
    status: str
    variance: float = 0.0


class Evidence(BaseModel):
    contract_source: str | None = None
    shipment_source: str | None = None
    load_source: str | None = None
    delivery_source: str | None = None


class MLResult(BaseModel):
    risk: str | None = None
    anomaly_score: float | None = None


class ExtractionResult(BaseModel):
    document_type: str = "freight_invoice"

    confidence: float | None = None

    needs_review: bool = False

    missing_fields: list[str] = Field(
        default_factory=list
    )

    review_reasons: list[str] = Field(
        default_factory=list
    )


class AuditResponse(BaseModel):
    # --------------------------------------------------------
    # IDENTIFIERS
    # --------------------------------------------------------

    invoice_id: str | None = None
    shipment_id: str | None = None
    load_id: str | None = None
    contract_id: str | None = None

    # --------------------------------------------------------
    # AUDIT RESULT
    # --------------------------------------------------------

    status: str = "REVIEW"
    severity: str = "LOW"

    # --------------------------------------------------------
    # EXTRACTION
    # --------------------------------------------------------

    extraction: ExtractionResult

    # --------------------------------------------------------
    # FINANCIAL RESULT
    # --------------------------------------------------------

    financial_summary: FinancialSummary

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    findings: list[Finding] = Field(
        default_factory=list
    )

    # --------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------

    checks: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    evidence: Evidence = Field(
        default_factory=Evidence
    )

    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    ml: MLResult = Field(
        default_factory=MLResult
    )

    # --------------------------------------------------------
    # MATCHING
    # --------------------------------------------------------

    matching: dict[str, Any] = Field(
        default_factory=dict
    )

    # --------------------------------------------------------
    # ORIGINAL NORMALIZED INVOICE
    # --------------------------------------------------------

    invoice: dict[str, Any] = Field(
        default_factory=dict
    )