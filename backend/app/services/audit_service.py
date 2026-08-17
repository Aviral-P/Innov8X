import sys
import tempfile
from pathlib import Path

from fastapi import UploadFile


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# EXISTING AUDIT PIPELINE
# ============================================================

from data.scripts.run_audit import run_audit


# ============================================================
# ML SERVICE
# ============================================================

from app.services.ml_service import predict_anomaly


# ============================================================
# SUPPORTED DOCUMENT TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".eml",
}


# ============================================================
# HELPERS
# ============================================================

def safe_float(
    value,
    default=0.0,
):
    """
    Convert a value to float without crashing on
    null, empty, currency-formatted, or malformed values.
    """

    if value is None:
        return default

    if isinstance(value, str):
        value = (
            value
            .replace("$", "")
            .replace(",", "")
            .strip()
        )

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def safe_list(
    value,
):
    """
    Always return a list for API fields
    that expect lists.
    """

    if isinstance(value, list):
        return value

    return []


# ============================================================
# ML RESULT BUILDER
# ============================================================

def build_ml_result(
    invoice_id,
) -> dict:
    """
    Look up the precomputed ML result for an invoice.

    ML is intentionally non-blocking:
    if an invoice does not exist in the ML output,
    the normal evidence audit can still be returned.
    """

    empty_result = {
        "risk": None,
        "anomaly_score": None,
    }

    if not invoice_id:
        return empty_result

    try:

        result = predict_anomaly(
            str(invoice_id)
        )

        return {
            "risk": result.get(
                "ml_risk"
            ),

            "anomaly_score": result.get(
                "anomaly_score"
            ),
        }

    except ValueError:

        return empty_result

    except Exception as exc:

        print(
            "ML prediction lookup failed:",
            exc,
        )

        return empty_result


# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_api_response(
    result: dict,
) -> dict:
    """
    Convert the internal audit pipeline result
    into the public API response.

    The response is intentionally tolerant of:

    - incomplete extraction
    - unmatched invoices
    - missing contracts
    - missing ML results
    - audits requiring manual review
    """

    result = result or {}

    # ========================================================
    # INTERNAL RESULT SECTIONS
    # ========================================================

    invoice = (
        result.get("invoice")
        or {}
    )

    matching = (
        result.get("matching")
        or {}
    )

    audit = (
        result.get("audit")
        or {}
    )

    finding_wrapper = (
        result.get("finding")
        or {}
    )

    finding_data = (
        finding_wrapper.get("finding")
        or {}
    )

    # ========================================================
    # EXTRACTION QUALITY
    # ========================================================

    extraction_metadata = (
        invoice.get(
            "extraction_metadata"
        )
        or {}
    )

    extraction = {
        "document_type": extraction_metadata.get(
            "document_type",
            "freight_invoice",
        ),

        "confidence": extraction_metadata.get(
            "confidence"
        ),

        "needs_review": bool(
            extraction_metadata.get(
                "needs_review",
                False,
            )
        ),

        "missing_fields": safe_list(
            extraction_metadata.get(
                "missing_critical_fields",
                [],
            )
        ),

        "review_reasons": safe_list(
            extraction_metadata.get(
                "review_reasons",
                [],
            )
        ),
    }

    # ========================================================
    # FINANCIAL SUMMARY
    # ========================================================

    financial_summary = {
        "billed_amount": safe_float(
            audit.get(
                "billed_total"
            )
        ),

        "expected_amount": safe_float(
            audit.get(
                "expected_total"
            )
        ),

        "overcharge_amount": safe_float(
            audit.get(
                "overcharge_amount"
            )
        ),
    }

    # ========================================================
    # FINDINGS
    # ========================================================

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

                "billed_amount": safe_float(
                    finding_data.get(
                        "billed_amount"
                    )
                ),

                "expected_amount": safe_float(
                    finding_data.get(
                        "expected_amount"
                    )
                ),

                "variance": safe_float(
                    finding_data.get(
                        "variance"
                    )
                ),

                "actual_distance_miles": (
                    safe_float(
                        finding_data.get(
                            "actual_distance_miles"
                        )
                    )
                    if finding_data.get(
                        "actual_distance_miles"
                    ) is not None
                    else None
                ),

                "contract_rate_per_mile": (
                    safe_float(
                        finding_data.get(
                            "contract_rate_per_mile"
                        )
                    )
                    if finding_data.get(
                        "contract_rate_per_mile"
                    ) is not None
                    else None
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

    # ========================================================
    # EVIDENCE
    # ========================================================

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

    # ========================================================
    # IDENTIFIERS
    # ========================================================

    invoice_id = audit.get(
        "invoice_id"
    )

    if invoice_id is None:
        invoice_id = invoice.get(
            "invoice_number"
        )

    shipment_id = audit.get(
        "shipment_id"
    )

    if shipment_id is None:
        shipment_id = matching.get(
            "shipment_id"
        )

    load_id = audit.get(
        "load_id"
    )

    if load_id is None:
        load_id = matching.get(
            "load_id"
        )

    contract_id = audit.get(
        "contract_id"
    )

    # ========================================================
    # ML ANOMALY DETECTION
    # ========================================================

    ml = build_ml_result(
        invoice_id
    )

    # ========================================================
    # AUDIT STATUS
    # ========================================================

    status = audit.get(
        "audit_status"
    )

    if not status:

        status = (
            "REVIEW"
            if matching.get(
                "match_status"
            ) != "MATCHED"
            else "UNKNOWN"
        )

    severity = (
        audit.get(
            "severity"
        )
        or "LOW"
    )

    # ========================================================
    # FINAL API RESPONSE
    # ========================================================

    return {
        "invoice_id": invoice_id,

        "shipment_id": shipment_id,

        "load_id": load_id,

        "contract_id": contract_id,

        "status": status,

        "severity": severity,

        "extraction": extraction,

        "financial_summary": financial_summary,

        "findings": findings,

        "checks": (
            audit.get(
                "checks",
                {},
            )
            or {}
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
    Save the uploaded document temporarily and
    run the existing Innov8X multimodal audit pipeline.

    Supported:

        PDF
        PNG
        JPG
        JPEG
        WEBP
        TIFF
        EML

    The original file extension is preserved so the
    multimodal extraction layer can determine how to
    process the document.
    """

    # ========================================================
    # FILE TYPE VALIDATION
    # ========================================================

    suffix = Path(
        invoice.filename or ""
    ).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            "Unsupported document type. "
            "Supported formats: PDF, PNG, JPG, JPEG, "
            "WEBP, TIFF and EML."
        )

    # ========================================================
    # READ UPLOAD
    # ========================================================

    contents = await invoice.read()

    if not contents:

        raise ValueError(
            "Uploaded invoice is empty."
        )

    temporary_path = None

    try:

        # ====================================================
        # TEMPORARY FILE
        # ====================================================

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temporary_file:

            temporary_file.write(
                contents
            )

            temporary_path = Path(
                temporary_file.name
            )

        print(
            f"Processing uploaded document: "
            f"{invoice.filename}"
        )

        print(
            f"Temporary document: "
            f"{temporary_path}"
        )

        # ====================================================
        # RUN EXISTING PIPELINE
        # ====================================================

        result = run_audit(
            temporary_path
        )

        # ====================================================
        # BUILD API RESPONSE
        # ====================================================

        return build_api_response(
            result
        )

    finally:

        # ====================================================
        # CLEANUP
        # ====================================================

        if (
            temporary_path is not None
            and temporary_path.exists()
        ):

            temporary_path.unlink()