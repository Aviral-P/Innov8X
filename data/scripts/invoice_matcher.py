import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVOICE_PATH = (
    PROJECT_ROOT
    / "data"
    / "openai_ocr_output.json"
)

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

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "matched_invoice.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    with open(
        INVOICE_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        invoice = json.load(f)

    invoices = pd.read_csv(
        INVOICES_PATH
    )

    shipments = pd.read_csv(
        SHIPMENTS_PATH
    )

    loads = pd.read_csv(
        LOADS_PATH
    )

    return (
        invoice,
        invoices,
        shipments,
        loads,
    )


# ============================================================
# EXACT IDENTIFIER MATCHING
# ============================================================

def match_invoice_by_identifiers(
    invoice,
    invoices,
    shipments,
    loads,
):
    """
    Match the OCR invoice using identifiers
    explicitly printed on the invoice.

    Priority:

        1. shipment_reference
        2. load_reference
        3. invoice_number

    Exact identifiers are preferred over
    fuzzy attribute matching.
    """

    shipment_reference = str(
        invoice.get("shipment_reference") or ""
    ).strip()

    load_reference = str(
        invoice.get("load_reference") or ""
    ).strip()

    invoice_number = str(
        invoice.get("invoice_number") or ""
    ).strip()

    # --------------------------------------------------------
    # 1. SHIPMENT REFERENCE
    # --------------------------------------------------------

    if shipment_reference:

        matches = shipments[
            shipments["shipment_id"]
            .astype(str)
            .str.strip()
            == shipment_reference
        ]

        if len(matches) == 1:

            row = matches.iloc[0]

            return {
                "match_status": "MATCHED",
                "confidence": "HIGH",
                "match_method": "shipment_reference",

                "shipment_id": row[
                    "shipment_id"
                ],

                "load_id": row[
                    "load_id"
                ],

                "trip_id": row[
                    "trip_id"
                ],

                "customer_id": row[
                    "customer_id"
                ],

                "route_id": row[
                    "route_id"
                ],
            }

        if len(matches) > 1:

            return {
                "match_status": "AMBIGUOUS",
                "confidence": "NONE",
                "match_method": "shipment_reference",
                "reason": (
                    "Shipment reference matched "
                    "multiple shipments."
                ),
            }

    # --------------------------------------------------------
    # 2. LOAD REFERENCE
    # --------------------------------------------------------

    if load_reference:

        matches = loads[
            loads["load_id"]
            .astype(str)
            .str.strip()
            == load_reference
        ]

        if len(matches) == 1:

            row = matches.iloc[0]

            return {
                "match_status": "MATCHED",
                "confidence": "HIGH",
                "match_method": "load_reference",

                "load_id": row[
                    "load_id"
                ],

                "customer_id": row[
                    "customer_id"
                ],

                "route_id": row[
                    "route_id"
                ],
            }

        if len(matches) > 1:

            return {
                "match_status": "AMBIGUOUS",
                "confidence": "NONE",
                "match_method": "load_reference",
                "reason": (
                    "Load reference matched "
                    "multiple loads."
                ),
            }

    # --------------------------------------------------------
    # 3. INVOICE NUMBER
    # --------------------------------------------------------

    if invoice_number:

        matches = invoices[
            invoices["invoice_id"]
            .astype(str)
            .str.strip()
            == invoice_number
        ]

        if len(matches) == 1:

            row = matches.iloc[0]

            return {
                "match_status": "MATCHED",
                "confidence": "HIGH",
                "match_method": "invoice_number",

                "invoice_id": row[
                    "invoice_id"
                ],

                "shipment_id": row[
                    "shipment_id"
                ],

                "load_id": row[
                    "load_id"
                ],

                "customer_id": row[
                    "customer_id"
                ],

                "route_id": row[
                    "route_id"
                ],

                "contract_id": row[
                    "contract_id"
                ],
            }

        if len(matches) > 1:

            return {
                "match_status": "AMBIGUOUS",
                "confidence": "NONE",
                "match_method": "invoice_number",
                "reason": (
                    "Invoice number matched "
                    "multiple billing records."
                ),
            }

    # --------------------------------------------------------
    # NO EXACT MATCH
    # --------------------------------------------------------

    return {
        "match_status": "UNMATCHED",
        "confidence": "NONE",
        "match_method": "none",
        "reason": (
            "No explicit invoice identifier "
            "matched the operational evidence."
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("Loading invoice...")
    print("Loading operational evidence...")

    (
        invoice,
        invoices,
        shipments,
        loads,
    ) = load_data()

    print(
        f"Shipments available: {len(shipments):,}"
    )

    print(
        "\nOCR identifiers:"
    )

    print(
        f"  Invoice:   "
        f"{invoice.get('invoice_number')}"
    )

    print(
        f"  Shipment:  "
        f"{invoice.get('shipment_reference')}"
    )

    print(
        f"  Load:      "
        f"{invoice.get('load_reference')}"
    )

    print(
        f"  Customer:  "
        f"{invoice.get('customer_id')}"
    )

    print(
        "\nMatching invoice..."
    )

    # --------------------------------------------------------
    # EXACT MATCH ONLY
    # --------------------------------------------------------

    result = match_invoice_by_identifiers(
        invoice,
        invoices,
        shipments,
        loads,
    )

    # --------------------------------------------------------
    # BUILD OUTPUT
    # --------------------------------------------------------

    output = {
        "invoice": invoice,
        "matching": result,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(
        "\nMatch result:"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
    )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()