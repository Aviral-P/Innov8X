import tempfile
from pathlib import Path

from fastapi import UploadFile


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SCRIPTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "scripts"
)


# ============================================================
# EXISTING AUDIT PIPELINE
# ============================================================


from data.scripts.run_audit import run_audit


# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_api_response(
    result: dict,
) -> dict:
    """
    Convert the internal audit pipeline result
    into the public API response format.
    """

    invoice = result.get(
        "invoice"
    ) or {}

    matching = result.get(
        "matching"
    ) or {}

    audit = result.get(
        "audit"
    ) or {}

    finding_wrapper = result.get(
        "finding"
    ) or {}

    finding_data = (
        finding_wrapper.get("finding")
        or {}
    )

    # --------------------------------------------------------
    # FINANCIAL SUMMARY
    # --------------------------------------------------------

    financial_summary = {
        "billed_amount": float(
            audit.get(
                "billed_total",
                0,
            )
        ),

        "expected_amount": float(
            audit.get(
                "expected_total",
                0,
            )
        ),

        "overcharge_amount": float(
            audit.get(
                "overcharge_amount",
                0,
            )
        ),
    }

    # --------------------------------------------------------
    # FINDINGS
    # --------------------------------------------------------

    findings = []

    if finding_data:

        findings.append(
            {
                "type": finding_data.get(
                    "type",
                    "unknown",
                ),

                "title": finding_data.get(
                    "title",
                    "Audit finding",
                ),

                "billed_amount": float(
                    finding_data.get(
                        "billed_amount",
                        0,
                    )
                ),

                "expected_amount": float(
                    finding_data.get(
                        "expected_amount",
                        0,
                    )
                ),

                "variance": float(
                    finding_data.get(
                        "variance",
                        0,
                    )
                ),

                "actual_distance_miles": (
                    finding_data.get(
                        "actual_distance_miles"
                    )
                ),

                "contract_rate_per_mile": (
                    finding_data.get(
                        "contract_rate_per_mile"
                    )
                ),

                "calculation": (
                    finding_data.get(
                        "calculation"
                    )
                ),

                "explanation": finding_data.get(
                    "explanation",
                    "",
                ),
            }
        )

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    audit_evidence = (
        audit.get(
            "evidence"
        )
        or {}
    )

    evidence = {
        "contract_source": audit_evidence.get(
            "contract_source"
        ),

        "shipment_source": audit_evidence.get(
            "shipment_source"
        ),

        "load_source": audit_evidence.get(
            "load_source"
        ),

        "delivery_source": audit_evidence.get(
            "delivery_source"
        ),
    }

    # --------------------------------------------------------
    # ML PLACEHOLDER
    # --------------------------------------------------------

    ml = {
        "risk": None,
        "anomaly_score": None,
    }

    # --------------------------------------------------------
    # FINAL API RESPONSE
    # --------------------------------------------------------

    return {
        "invoice_id": audit.get(
            "invoice_id",
            invoice.get(
                "invoice_number"
            ),
        ),

        "shipment_id": audit.get(
            "shipment_id",
            matching.get(
                "shipment_id"
            ),
        ),

        "load_id": audit.get(
            "load_id",
            matching.get(
                "load_id"
            ),
        ),

        "contract_id": audit.get(
            "contract_id"
        ),

        "status": audit.get(
            "audit_status",
            "UNKNOWN",
        ),

        "severity": audit.get(
            "severity",
            "UNKNOWN",
        ),

        "financial_summary": financial_summary,

        "findings": findings,

        "checks": audit.get(
            "checks",
            {},
        ),

        "evidence": evidence,

        "ml": ml,

        "matching": matching,

        "invoice": invoice,
    }


# ============================================================
# AUDIT SERVICE
# ============================================================

async def audit_invoice(
    invoice: UploadFile,
) -> dict:
    """
    Save the uploaded invoice temporarily and
    run the existing Innov8X audit pipeline.
    """

    suffix = Path(
        invoice.filename or "invoice.pdf"
    ).suffix.lower()

    if suffix != ".pdf":
        raise ValueError(
            "Only PDF invoices are supported."
        )

    contents = await invoice.read()

    if not contents:
        raise ValueError(
            "Uploaded invoice is empty."
        )

    temporary_path = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temporary_file:

            temporary_file.write(
                contents
            )

            temporary_path = Path(
                temporary_file.name
            )

        result = run_audit(
            temporary_path
        )

        return build_api_response(
            result
        )

    finally:

        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()