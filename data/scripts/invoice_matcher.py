import json
import re
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
# NORMALIZATION HELPERS
# ============================================================

def normalize_value(value) -> str:
    """
    Normalize identifiers and textual values before comparison.

    Examples:

        " SHP-123 " -> "shp123"
        "INV 001"   -> "inv001"
        "Miami, FL" -> "miami fl"
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "",
        value,
    )

    return value


def normalize_text(value) -> str:
    """
    Normalize natural-language fields such as cities,
    carrier names, and addresses.
    """

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def safe_value(row, column):
    """
    Safely retrieve a dataframe column value.
    """

    if column not in row.index:
        return None

    value = row[column]

    if pd.isna(value):
        return None

    return value


def first_invoice_value(
    invoice: dict,
    *keys,
):
    """
    Return the first non-empty value from an invoice.
    """

    for key in keys:

        value = invoice.get(key)

        if value is None:
            continue

        if isinstance(value, str):
            if not value.strip():
                continue

        return value

    return None


# ============================================================
# DATA LOADING
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
# COLUMN DISCOVERY
# ============================================================

def find_column(
    dataframe,
    candidates,
):
    """
    Find the first available column from a list
    of semantic candidates.

    This allows the matcher to work with datasets
    whose column names are not identical.
    """

    normalized_columns = {
        normalize_value(column): column
        for column in dataframe.columns
    }

    for candidate in candidates:

        normalized_candidate = (
            normalize_value(candidate)
        )

        if normalized_candidate in normalized_columns:

            return normalized_columns[
                normalized_candidate
            ]

    return None


def find_columns(
    dataframe,
    candidates,
):
    """
    Return all matching columns from candidate names.
    """

    results = []

    normalized_columns = {
        normalize_value(column): column
        for column in dataframe.columns
    }

    for candidate in candidates:

        normalized_candidate = (
            normalize_value(candidate)
        )

        if normalized_candidate in normalized_columns:

            results.append(
                normalized_columns[
                    normalized_candidate
                ]
            )

    return results


# ============================================================
# RESULT BUILDER
# ============================================================

def build_match_result(
    *,
    status,
    confidence,
    method,
    reason=None,
    row=None,
):

    result = {
        "match_status": status,
        "confidence": confidence,
        "match_method": method,
    }

    if reason:
        result["reason"] = reason

    if row is not None:

        fields = [
            "invoice_id",
            "shipment_id",
            "load_id",
            "trip_id",
            "customer_id",
            "route_id",
            "contract_id",
        ]

        for field in fields:

            if field in row.index:

                value = safe_value(
                    row,
                    field,
                )

                if value is not None:

                    result[field] = value

    return result


# ============================================================
# EXACT IDENTIFIER MATCHING
# ============================================================

def exact_identifier_match(
    invoice,
    dataframe,
    identifier_mapping,
):
    """
    Try exact semantic identifier matching.

    identifier_mapping:

        {
            "shipment_reference": [
                "shipment_id",
                "shipment_reference",
            ],

            "load_reference": [
                "load_id",
                "load_reference",
            ],

            ...
        }
    """

    for invoice_key, dataframe_columns in (
        identifier_mapping.items()
    ):

        invoice_value = first_invoice_value(
            invoice,
            invoice_key,
        )

        normalized_invoice_value = (
            normalize_value(invoice_value)
        )

        if not normalized_invoice_value:
            continue

        available_columns = find_columns(
            dataframe,
            dataframe_columns,
        )

        for column in available_columns:

            normalized_column = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .map(normalize_value)
            )

            matches = dataframe[
                normalized_column
                == normalized_invoice_value
            ]

            if len(matches) == 1:

                return (
                    matches.iloc[0],
                    invoice_key,
                    column,
                )

            if len(matches) > 1:

                return (
                    "AMBIGUOUS",
                    invoice_key,
                    column,
                )

    return (
        None,
        None,
        None,
    )


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date(value):

    if value is None:
        return None

    try:

        parsed = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(parsed):
            return None

        return parsed.strftime(
            "%Y-%m-%d"
        )

    except Exception:

        return None


# ============================================================
# ROUTE EXTRACTION
# ============================================================

def get_invoice_origin(
    invoice,
):
    return first_invoice_value(
        invoice,
        "pickup_address",
        "origin",
        "origin_address",
        "pickup_location",
    )


def get_invoice_destination(
    invoice,
):
    return first_invoice_value(
        invoice,
        "destination_address",
        "destination",
        "destination_address",
        "delivery_location",
    )


def route_component_match(
    invoice_value,
    row_value,
):
    """
    Conservative comparison for route components.

    Example:

        Miami, FL
        Miami, Florida

    Exact normalization is preferred.
    """

    invoice_normalized = normalize_text(
        invoice_value
    )

    row_normalized = normalize_text(
        row_value
    )

    if not invoice_normalized or not row_normalized:
        return False

    return (
        normalize_value(
            invoice_normalized
        )
        == normalize_value(
            row_normalized
        )
    )


# ============================================================
# FLEXIBLE ATTRIBUTE MATCHING
# ============================================================

def flexible_candidate_matching(
    invoice,
    shipments,
    loads,
):
    """
    Find operational evidence when explicit identifiers
    are unavailable.

    Matching uses multiple independent attributes.

    Strong attributes:

        customer
        origin
        destination
        date

    The matcher does NOT accept a route-only match.
    """

    shipment = shipments.copy()

    if shipment.empty:

        return {
            "match_status": "UNMATCHED",
            "confidence": "NONE",
            "match_method": "attribute_matching",
            "reason": (
                "No shipment evidence is available."
            ),
        }

    origin = get_invoice_origin(
        invoice
    )

    destination = get_invoice_destination(
        invoice
    )

    invoice_date = normalize_date(
        first_invoice_value(
            invoice,
            "invoice_date",
            "shipment_date",
        )
    )

    customer_id = first_invoice_value(
        invoice,
        "customer_id",
    )

    carrier_name = first_invoice_value(
        invoice,
        "carrier_name",
    )

    # --------------------------------------------------------
    # DISCOVER DATASET COLUMNS
    # --------------------------------------------------------

    origin_column = find_column(
        shipment,
        [
            "origin",
            "origin_city",
            "pickup",
            "pickup_city",
            "pickup_location",
            "origin_address",
        ],
    )

    destination_column = find_column(
        shipment,
        [
            "destination",
            "destination_city",
            "delivery",
            "delivery_city",
            "delivery_location",
            "destination_address",
        ],
    )

    date_column = find_column(
        shipment,
        [
            "shipment_date",
            "pickup_date",
            "load_date",
            "ship_date",
            "date",
        ],
    )

    customer_column = find_column(
        shipment,
        [
            "customer_id",
            "customer",
            "customer_reference",
        ],
    )

    carrier_column = find_column(
        shipment,
        [
            "carrier_name",
            "carrier",
        ],
    )

    # --------------------------------------------------------
    # SCORE CANDIDATES
    # --------------------------------------------------------

    candidates = []

    for index, row in shipment.iterrows():

        score = 0
        matched_attributes = []

        # Customer
        if (
            customer_id
            and customer_column
        ):

            if (
                normalize_value(
                    customer_id
                )
                == normalize_value(
                    safe_value(
                        row,
                        customer_column,
                    )
                )
            ):

                score += 30

                matched_attributes.append(
                    "customer"
                )

        # Origin
        if (
            origin
            and origin_column
        ):

            if route_component_match(
                origin,
                safe_value(
                    row,
                    origin_column,
                ),
            ):

                score += 25

                matched_attributes.append(
                    "origin"
                )

        # Destination
        if (
            destination
            and destination_column
        ):

            if route_component_match(
                destination,
                safe_value(
                    row,
                    destination_column,
                ),
            ):

                score += 25

                matched_attributes.append(
                    "destination"
                )

        # Date
        if (
            invoice_date
            and date_column
        ):

            row_date = normalize_date(
                safe_value(
                    row,
                    date_column,
                )
            )

            if (
                row_date
                and row_date == invoice_date
            ):

                score += 20

                matched_attributes.append(
                    "date"
                )

        # Carrier
        if (
            carrier_name
            and carrier_column
        ):

            if normalize_value(
                carrier_name
            ) == normalize_value(
                safe_value(
                    row,
                    carrier_column,
                )
            ):

                score += 10

                matched_attributes.append(
                    "carrier"
                )

        if score > 0:

            candidates.append(
                {
                    "index": index,
                    "score": score,
                    "matched_attributes": (
                        matched_attributes
                    ),
                }
            )

    if not candidates:

        return {
            "match_status": "UNMATCHED",
            "confidence": "NONE",
            "match_method": "attribute_matching",
            "reason": (
                "No operational record matched "
                "the available invoice attributes."
            ),
        }

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    best = candidates[0]

    # --------------------------------------------------------
    # AMBIGUITY PROTECTION
    # --------------------------------------------------------

    if len(candidates) > 1:

        second = candidates[1]

        if (
            best["score"]
            == second["score"]
        ):

            return {
                "match_status": "AMBIGUOUS",
                "confidence": "NONE",
                "match_method": "attribute_matching",
                "reason": (
                    "Multiple operational records "
                    "matched with equal confidence."
                ),
                "candidate_count": len(
                    candidates
                ),
            }

    row = shipment.loc[
        best["index"]
    ]

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    if best["score"] >= 80:

        confidence = "HIGH"

    elif best["score"] >= 60:

        confidence = "MEDIUM"

    else:

        confidence = "LOW"

    # We don't want a weak route-only match to
    # silently drive a financial audit.

    if best["score"] < 60:

        return {
            "match_status": "UNMATCHED",
            "confidence": confidence,
            "match_method": "attribute_matching",
            "reason": (
                "A possible operational record was "
                "found, but the evidence was not "
                "strong enough for an automatic audit."
            ),
            "candidate_count": len(
                candidates
            ),
            "matched_attributes": (
                best["matched_attributes"]
            ),
        }

    result = build_match_result(
        status="MATCHED",
        confidence=confidence,
        method="attribute_matching",
        row=row,
    )

    result["matched_attributes"] = (
        best["matched_attributes"]
    )

    result["candidate_count"] = len(
        candidates
    )

    return result


# ============================================================
# MAIN MATCHER
# ============================================================

def match_invoice_by_identifiers(
    invoice,
    invoices,
    shipments,
    loads,
):
    """
    Flexible evidence matcher.

    Matching priority:

        1. Shipment reference
        2. Load reference
        3. PRO number
        4. BOL number
        5. PO number
        6. Carrier reference
        7. Invoice number
        8. Customer + route + date

    Exact identifier matches are preferred.

    Attribute matching is used only when explicit operational
    identifiers are unavailable. If an explicit operational
    identifier is present but cannot be matched, the invoice
    remains UNMATCHED rather than being attached to a weak
    attribute-based candidate.

    The matcher never invents an operational record.
    """

    # ========================================================
    # 1. SHIPMENT / LOAD / OTHER IDENTIFIERS
    # ========================================================

    shipment_mapping = {
        "shipment_reference": [
            "shipment_id",
            "shipment_reference",
        ],

        "load_reference": [
            "load_id",
            "load_reference",
        ],

        "pro_number": [
            "pro_number",
            "pro",
            "pro_id",
        ],

        "bol_number": [
            "bol_number",
            "bol",
            "bill_of_lading",
        ],

        "po_number": [
            "po_number",
            "po",
            "purchase_order",
        ],

        "carrier_reference": [
            "carrier_reference",
            "carrier_id",
            "carrier_ref",
        ],

        "invoice_number": [
            "invoice_id",
            "invoice_number",
        ],
    }

    shipment_result = exact_identifier_match(
        invoice,
        shipments,
        shipment_mapping,
    )

    row = shipment_result[0]
    matched_invoice_key = shipment_result[1]
    matched_column = shipment_result[2]

    if isinstance(row, str) and row == "AMBIGUOUS":

        return {
            "match_status": "AMBIGUOUS",
            "confidence": "NONE",
            "match_method": matched_invoice_key,
            "reason": (
                f"{matched_invoice_key} matched "
                "multiple operational records."
            ),
        }

    if row is not None:

        result = build_match_result(
            status="MATCHED",
            confidence="HIGH",
            method=matched_invoice_key,
            row=row,
        )

        result["matched_column"] = (
            matched_column
        )

        return result

    # ========================================================
    # 2. INVOICE BILLING RECORD
    # ========================================================

    invoice_mapping = {
        "invoice_number": [
            "invoice_id",
            "invoice_number",
        ],

        "po_number": [
            "po_number",
            "po",
            "purchase_order",
        ],

        "bol_number": [
            "bol_number",
            "bol",
            "bill_of_lading",
        ],

        "pro_number": [
            "pro_number",
            "pro",
            "pro_id",
        ],
    }

    invoice_result = exact_identifier_match(
        invoice,
        invoices,
        invoice_mapping,
    )

    row = invoice_result[0]
    matched_invoice_key = invoice_result[1]
    matched_column = invoice_result[2]

    if isinstance(row, str) and row == "AMBIGUOUS":

        return {
            "match_status": "AMBIGUOUS",
            "confidence": "NONE",
            "match_method": matched_invoice_key,
            "reason": (
                f"{matched_invoice_key} matched "
                "multiple billing records."
            ),
        }

    if row is not None:

        result = build_match_result(
            status="MATCHED",
            confidence="HIGH",
            method=matched_invoice_key,
            row=row,
        )

        result["matched_column"] = (
            matched_column
        )

        return result

    # ========================================================
    # 3. PROTECT AGAINST FALSE ATTRIBUTE MATCHES
    # ========================================================
    #
    # If the invoice explicitly provides an operational
    # identifier (shipment/load/PRO/BOL/PO/carrier reference)
    # and that identifier did not match the evidence, do NOT
    # fall back to weak attribute matching.
    #
    # This is critical for evidence-driven auditing:
    #
    #   SHP-123456 != some unrelated shipment
    #
    # We would rather return UNMATCHED and request more
    # evidence than attach the invoice to the wrong shipment.
    # ========================================================

    operational_identifier_keys = (
        "shipment_reference",
        "load_reference",
        "pro_number",
        "bol_number",
        "po_number",
        "carrier_reference",
    )

    supplied_identifiers = [
        key
        for key in operational_identifier_keys
        if first_invoice_value(invoice, key) is not None
        and str(first_invoice_value(invoice, key)).strip()
    ]

    if supplied_identifiers:

        return {
            "match_status": "UNMATCHED",
            "confidence": "NONE",
            "match_method": "explicit_identifier_not_found",
            "reason": (
                "The invoice contains explicit operational "
                "identifier(s), but none matched the available "
                "operational or billing evidence. Attribute "
                "matching was intentionally skipped to prevent "
                "assigning the invoice to an unrelated shipment."
            ),
            "unmatched_identifiers": {
                key: first_invoice_value(invoice, key)
                for key in supplied_identifiers
            },
        }

    # ========================================================
    # 4. FLEXIBLE ATTRIBUTE MATCHING
    # ========================================================
    #
    # Attribute matching is only appropriate when the invoice
    # does not contain usable explicit operational identifiers.
    # ========================================================

    return flexible_candidate_matching(
        invoice,
        shipments,
        loads,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading invoice..."
    )

    print(
        "Loading operational evidence..."
    )

    (
        invoice,
        invoices,
        shipments,
        loads,
    ) = load_data()

    print(
        f"Shipments available: "
        f"{len(shipments):,}"
    )

    print(
        "\nExtracted identifiers:"
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
        f"  PRO:       "
        f"{invoice.get('pro_number')}"
    )

    print(
        f"  BOL:       "
        f"{invoice.get('bol_number')}"
    )

    print(
        f"  PO:        "
        f"{invoice.get('po_number')}"
    )

    print(
        f"  Customer:  "
        f"{invoice.get('customer_id')}"
    )

    print(
        "\nMatching invoice..."
    )

    result = match_invoice_by_identifiers(
        invoice,
        invoices,
        shipments,
        loads,
    )

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