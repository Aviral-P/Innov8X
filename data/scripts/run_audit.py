import json
import sys
from pathlib import Path

import pandas as pd

from data.scripts.openai_invoice import extract_invoice
from data.scripts.normalize_invoice import normalize_invoice
from data.scripts.normalize_invoice import normalize_invoice
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
# PIPELINE
# ============================================================

def run_audit(invoice_path):

    print("=" * 60)
    print("              INNOV8X INVOICE AUDIT")
    print("=" * 60)

    print(
        f"\nInvoice: {invoice_path}"
    )

    # --------------------------------------------------------
    # 1. MULTIMODAL EXTRACTION + NORMALIZATION
    # --------------------------------------------------------

    print(
        "\n[1/5] Extracting and understanding invoice..."
    )

    raw_invoice = extract_invoice(
        invoice_path
    )

    invoice = normalize_invoice(
        raw_invoice
    )

    invoice = normalize_invoice(
        raw_invoice
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

    extraction_metadata = (
        invoice.get(
            "extraction_metadata"
        )
        or {}
    )

    print(
        f"Extraction confidence: "
        f"{extraction_metadata.get('classifier_confidence')}"
    )

    if extraction_metadata.get(
        "needs_review",
        False,
    ):

        print(
            "Warning: extraction requires review."
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

    if matching.get(
        "match_status"
    ) != "MATCHED":

        result = {
            "invoice": invoice,
            "matching": matching,
            "audit": None,
            "finding": None,
        }

        OUTPUT_PATH.write_text(
            json.dumps(
                result,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            "\nAudit stopped:"
        )

        print(
            json.dumps(
                matching,
                indent=2,
                default=str,
            )
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

    for error in audit["error_types"]:

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
            "python data/scripts/run_audit.py "
            "<invoice>"
        )

        print(
            "\nSupported formats:"
        )

        for extension in sorted(
            SUPPORTED_EXTENSIONS
        ):
            print(
                f"  {extension}"
            )

        sys.exit(1)

    invoice_path = Path(
        sys.argv[1]
    ).expanduser().resolve()

    if not invoice_path.exists():

        print(
            "ERROR: Invoice/document not found:"
        )

        print(
            invoice_path
        )

        sys.exit(1)

    if invoice_path.suffix.lower() not in (
        SUPPORTED_EXTENSIONS
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

        message = str(exc)

        if message.startswith(
            "INVALID_INVOICE:"
        ):

            reason = message[
                len("INVALID_INVOICE:")
            ].strip()

            print(
                "\nINVALID DOCUMENT"
            )

            print(
                "Kindly upload a valid freight invoice."
            )

            if reason:
                print(
                    f"Reason: {reason}"
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


if __name__ == "__main__":
    main()