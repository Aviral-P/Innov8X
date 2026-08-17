import json
import sys
from pathlib import Path

import pandas as pd

from data.scripts.openai_invoice import (
    extract_invoice,
    SUPPORTED_EXTENSIONS,
)
from data.scripts.invoice_matcher import (
    match_invoice_by_identifiers,
)
from data.scripts.invoice_auditor import audit_invoice
from data.scripts.finding_builder import build_finding


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVOICES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "invoices.csv"
)

SHIPMENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "shipment_evidence.csv"
)

LOADS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "load_evidence.csv"
)

DELIVERIES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "delivery_evidence.csv"
)

CONTRACTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "contract_rates.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "final_audit_result.json"
)


# ============================================================
# DATA LOADING
# ============================================================

def load_evidence():

    invoices = pd.read_csv(
        INVOICES_PATH
    )

    shipments = pd.read_csv(
        SHIPMENTS_PATH
    )

    loads = pd.read_csv(
        LOADS_PATH
    )

    deliveries = pd.read_csv(
        DELIVERIES_PATH
    )

    contracts = pd.read_csv(
        CONTRACTS_PATH
    )

    return (
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    )


# ============================================================
# INSUFFICIENT EVIDENCE RESULT
# ============================================================

def build_insufficient_evidence_result(
    invoice,
    matching,
):
    """
    Build a safe result when the invoice cannot be
    reliably connected to operational evidence.

    IMPORTANT:
    We deliberately do not perform a financial audit
    without sufficient evidence.
    """

    return {
        "invoice": invoice,

        "matching": matching,

        "audit": {
            "invoice_id": (
                invoice.get("invoice_number")
                or "UNKNOWN"
            ),

            "shipment_id": (
                matching.get("shipment_id")
                or "NOT_AVAILABLE"
            ),

            "load_id": (
                matching.get("load_id")
                or "NOT_AVAILABLE"
            ),

            "contract_id": (
                matching.get("contract_id")
                or "NOT_AVAILABLE"
            ),

            "audit_status": (
                "INSUFFICIENT_EVIDENCE"
            ),

            "error_types": [],

            "overcharge_amount": 0.0,

            "severity": "REVIEW",

            "billed_total": (
                float(
                    invoice.get(
                        "grand_total"
                    ) or 0
                )
            ),

            "expected_total": 0.0,

            "total_variance": 0.0,

            "checks": {},

            "evidence": {},

            "review_reason": (
                matching.get(
                    "reason",
                    "The invoice could not be "
                    "reliably matched to operational "
                    "evidence.",
                )
            ),
        },

        "finding": None,
    }


# ============================================================
# PIPELINE
# ============================================================

def run_audit(invoice_path):

    invoice_path = Path(
        invoice_path
    ).expanduser().resolve()

    print("=" * 60)
    print(
        "              INNOV8X INVOICE AUDIT"
    )
    print("=" * 60)

    print(
        f"\nInvoice: {invoice_path}"
    )

    # --------------------------------------------------------
    # 1. MULTIMODAL EXTRACTION
    # --------------------------------------------------------

    print(
        "\n[1/5] Extracting and understanding invoice..."
    )

    invoice = extract_invoice(
        invoice_path
    )

    print(
        f"Invoice ID: "
        f"{invoice.get('invoice_number')}"
    )

    print(
        f"Shipment reference: "
        f"{invoice.get('shipment_reference')}"
    )

    print(
        f"Load reference: "
        f"{invoice.get('load_reference')}"
    )

    print(
        f"Extraction confidence: "
        f"{invoice.get('extraction_metadata', {}).get('confidence')}"
    )

    extraction_metadata = (
        invoice.get(
            "extraction_metadata"
        )
        or {}
    )

    if extraction_metadata.get(
        "needs_review"
    ):

        print(
            "Warning: extraction requires review."
        )

        review_reasons = (
            extraction_metadata.get(
                "review_reasons"
            )
            or []
        )

        for reason in review_reasons:

            print(
                f"  - {reason}"
            )

    # --------------------------------------------------------
    # 2. LOAD EVIDENCE
    # --------------------------------------------------------

    print(
        "\n[2/5] Loading operational evidence..."
    )

    (
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    ) = load_evidence()

    print(
        f"Shipments available: "
        f"{len(shipments):,}"
    )

    print(
        f"Loads available: "
        f"{len(loads):,}"
    )

    print(
        f"Contracts available: "
        f"{len(contracts):,}"
    )

    # --------------------------------------------------------
    # 3. MATCH
    # --------------------------------------------------------

    print(
        "\n[3/5] Matching invoice..."
    )

    matching = match_invoice_by_identifiers(
        invoice,
        invoices,
        shipments,
        loads,
    )

    print(
        f"Match status: "
        f"{matching.get('match_status')}"
    )

    print(
        f"Confidence: "
        f"{matching.get('confidence')}"
    )

    print(
        f"Match method: "
        f"{matching.get('match_method')}"
    )

    if matching.get(
        "matched_attributes"
    ):

        print(
            "Matched attributes: "
            + ", ".join(
                matching[
                    "matched_attributes"
                ]
            )
        )

    # --------------------------------------------------------
    # NO RELIABLE EVIDENCE
    # --------------------------------------------------------

    if matching.get(
        "match_status"
    ) != "MATCHED":

        print(
            "\nEvidence matching was not sufficient "
            "for an automatic financial audit."
        )

        result = (
            build_insufficient_evidence_result(
                invoice,
                matching,
            )
        )

        OUTPUT_PATH.write_text(
            json.dumps(
                result,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            "\n============================================================"
        )

        print(
            "             AUDIT REQUIRES REVIEW"
        )

        print(
            "============================================================"
        )

        print(
            f"Status: "
            f"INSUFFICIENT_EVIDENCE"
        )

        print(
            f"Reason: "
            f"{matching.get('reason')}"
        )

        print(
            "\nNo financial conclusion was generated."
        )

        print(
            "Additional operational evidence is required."
        )

        print(
            f"\nSaved to:"
        )

        print(
            OUTPUT_PATH
        )

        print(
            "============================================================"
        )

        return result

    # --------------------------------------------------------
    # 4. DETERMINISTIC AUDIT
    # --------------------------------------------------------

    print(
        "\n[4/5] Running evidence audit..."
    )

    matched = {
        "invoice": invoice,
        "matching": matching,
    }

    audit = audit_invoice(
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    )

    print(
        f"Audit status: "
        f"{audit['audit_status']}"
    )

    print(
        f"Severity: "
        f"{audit['severity']}"
    )

    print(
        f"Potential overcharge: "
        f"${audit['overcharge_amount']:.2f}"
    )

    # --------------------------------------------------------
    # 5. FINDING
    # --------------------------------------------------------

    print(
        "\n[5/5] Building evidence-backed finding..."
    )

    finding = build_finding(
        audit
    )

    result = {
        "invoice": invoice,
        "matching": matching,
        "audit": audit,
        "finding": finding,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            result,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "                 FINAL RESULT"
    )

    print(
        "=" * 60
    )

    print(
        f"Invoice:     "
        f"{audit['invoice_id']}"
    )

    print(
        f"Shipment:    "
        f"{audit['shipment_id']}"
    )

    print(
        f"Load:        "
        f"{audit['load_id']}"
    )

    print(
        f"Status:      "
        f"{audit['audit_status']}"
    )

    print(
        f"Severity:    "
        f"{audit['severity']}"
    )

    print(
        f"Exposure:    "
        f"${audit['overcharge_amount']:.2f}"
    )

    print(
        "\nFindings:"
    )

    for error in audit[
        "error_types"
    ]:

        print(
            f"  - {error}"
        )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_PATH
    )

    print(
        "=" * 60
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "python -m data.scripts.run_audit "
            "<invoice>"
        )

        print(
            "\nSupported formats:"
        )

        print(
            ", ".join(
                sorted(
                    SUPPORTED_EXTENSIONS
                )
            )
        )

        sys.exit(1)

    invoice_path = Path(
        sys.argv[1]
    ).expanduser().resolve()

    if not invoice_path.exists():

        print(
            "ERROR: Invoice not found:"
        )

        print(
            invoice_path
        )

        sys.exit(1)

    if (
        invoice_path.suffix.lower()
        not in SUPPORTED_EXTENSIONS
    ):

        print(
            "ERROR: Unsupported document type."
        )

        print(
            "Supported formats:"
        )

        print(
            ", ".join(
                sorted(
                    SUPPORTED_EXTENSIONS
                )
            )
        )

        sys.exit(1)

    try:

        run_audit(
            invoice_path
        )

    except ValueError as exc:

        # ----------------------------------------------------
        # INVALID DOCUMENT
        # ----------------------------------------------------

        message = str(exc)

        if message.startswith(
            "INVALID_INVOICE:"
        ):

            reason = message.replace(
                "INVALID_INVOICE:",
                "",
                1,
            )

            print(
                "\n============================================================"
            )

            print(
                "             INVALID INVOICE"
            )

            print(
                "============================================================"
            )

            print(
                "Kindly upload a valid freight invoice."
            )

            print(
                f"Reason: {reason}"
            )

            print(
                "============================================================"
            )

            sys.exit(2)

        raise

    except Exception as exc:

        print(
            "\nAUDIT PIPELINE FAILED"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()