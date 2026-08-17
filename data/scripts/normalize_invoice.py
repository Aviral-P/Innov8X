import json
import re
from typing import Any


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def clean_number(value: Any) -> float | None:
    """
    Convert invoice numeric values into floats.

    Examples:
        "4,500.00" -> 4500.0
        "$4,500.00" -> 4500.0
        "₹4,500.00" -> 4500.0
        4500 -> 4500.0
        None -> None
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if not value:
        return None

    # Remove common currency symbols and separators.
    cleaned = re.sub(
        r"[$€£₹,\s]",
        "",
        value,
    )

    # Keep digits, decimal point and minus sign.
    cleaned = re.sub(
        r"[^0-9.\-]",
        "",
        cleaned,
    )

    if not cleaned:
        return None

    try:
        return float(cleaned)

    except ValueError:
        return None


def clean_text(value: Any) -> str | None:
    """
    Normalize text fields.

    Empty strings become None.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


# ============================================================
# CHARGE TYPE NORMALIZATION
# ============================================================

CHARGE_ALIASES = {

    # Transportation / linehaul
    "linehaul": "transportation",
    "line haul": "transportation",
    "freight": "transportation",
    "freight charge": "transportation",
    "freight charges": "transportation",
    "transportation": "transportation",
    "transportation charge": "transportation",
    "transportation charges": "transportation",
    "base freight": "transportation",
    "base rate": "transportation",
    "linehaul charge": "transportation",
    "line haul charge": "transportation",

    # Fuel
    "fuel": "fuel",
    "fuel charge": "fuel",
    "fuel surcharge": "fuel",
    "fuel adjustment": "fuel",
    "fsc": "fuel",
    "f.s.c.": "fuel",

    # Detention
    "detention": "detention",
    "detention charge": "detention",
    "detention fee": "detention",
    "waiting": "detention",
    "waiting time": "detention",
    "waiting fee": "detention",
    "wait time": "detention",

    # Accessorial
    "accessorial": "accessorial",
    "accessorial charge": "accessorial",
    "accessorial charges": "accessorial",

    # Permit
    "permit": "permit",
    "permits": "permit",
    "permit charge": "permit",
    "permit fee": "permit",

    # Escort
    "escort": "escort",
    "escorts": "escort",
    "escort charge": "escort",
    "escort fee": "escort",

    # Special handling
    "special handling": "special_handling",
    "special handling charge": "special_handling",
    "special handling fee": "special_handling",
}


def normalize_charge_type(
    value: Any,
) -> str:
    """
    Convert different freight terminology into a
    canonical charge category.

    Unknown terminology is preserved as 'unknown'.
    """

    if value is None:
        return "unknown"

    text = str(value).strip().lower()

    if not text:
        return "unknown"

    # Direct alias lookup.
    if text in CHARGE_ALIASES:
        return CHARGE_ALIASES[text]

    # Fuzzy semantic matching for common variations.
    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    ).strip()

    if (
        "linehaul" in normalized
        or "line haul" in normalized
        or "freight" in normalized
        or "transportation" in normalized
    ):
        return "transportation"

    if (
        "fuel surcharge" in normalized
        or normalized == "fsc"
        or normalized.startswith("fuel ")
    ):
        return "fuel"

    if (
        "detention" in normalized
        or "waiting time" in normalized
        or "wait time" in normalized
    ):
        return "detention"

    if "accessorial" in normalized:
        return "accessorial"

    if "permit" in normalized:
        return "permit"

    if "escort" in normalized:
        return "escort"

    if "special handling" in normalized:
        return "special_handling"

    return "unknown"


# ============================================================
# ADDITIONAL CHARGES
# ============================================================

def normalize_additional_charges(
    raw_charges: Any,
) -> list[dict]:
    """
    Normalize additional invoice line items.

    Unknown charges are intentionally preserved instead
    of being discarded.
    """

    if not isinstance(raw_charges, list):
        return []

    normalized = []

    for charge in raw_charges:

        if not isinstance(charge, dict):
            continue

        description = clean_text(
            charge.get("description")
        )

        amount = clean_number(
            charge.get("amount")
        )

        normalized_type = (
            charge.get("normalized_type")
        )

        if normalized_type:

            normalized_type = normalize_charge_type(
                normalized_type
            )

        else:

            normalized_type = normalize_charge_type(
                description
            )

        normalized.append(
            {
                "description": description,
                "amount": amount,
                "normalized_type": normalized_type,
            }
        )

    return normalized


# ============================================================
# EXTRACTION METADATA
# ============================================================

def normalize_extraction_metadata(
    raw: Any,
) -> dict:
    """
    Preserve document classification and extraction
    confidence information.
    """

    if not isinstance(raw, dict):
        raw = {}

    confidence = clean_number(
        raw.get("confidence")
    )

    classifier_confidence = clean_number(
        raw.get("classifier_confidence")
    )

    needs_review = raw.get(
        "needs_review",
        False,
    )

    if not isinstance(needs_review, bool):
        needs_review = bool(
            needs_review
        )

    return {
        "document_type": (
            clean_text(
                raw.get(
                    "document_type",
                    "freight_invoice",
                )
            )
            or "freight_invoice"
        ),

        "confidence": confidence,

        "classifier_confidence": (
            classifier_confidence
        ),

        "classifier_reason": clean_text(
            raw.get(
                "classifier_reason"
            )
        ),

        "needs_review": needs_review,
    }


# ============================================================
# CANONICAL INVOICE NORMALIZATION
# ============================================================

def calculate_grand_total(
    raw: dict,
) -> float | None:
    """
    Derive the invoice total from canonical charge fields
    when the invoice does not explicitly provide a grand total.

    If an explicit grand total exists, preserve it.

    Otherwise calculate:

        transportation
        + fuel
        + accessorial
        + detention
        + permits
        + escorts
        + special handling
    """

    # --------------------------------------------------------
    # 1. Prefer explicit invoice total
    # --------------------------------------------------------

    explicit_total = clean_number(
        raw.get("grand_total")
    )

    if explicit_total is not None:
        return explicit_total

    # --------------------------------------------------------
    # 2. Calculate total from known charge fields
    # --------------------------------------------------------

    charge_fields = [
        "transportation_charge",
        "fuel_charge",
        "accessorial_charge",
        "detention_charge",
        "permits_charge",
        "escorts_charge",
        "special_handling_charge",
    ]

    total = 0.0
    found_charge = False

    for field in charge_fields:

        value = clean_number(
            raw.get(field)
        )

        if value is not None:

            total += value
            found_charge = True

    # --------------------------------------------------------
    # 3. No usable charges
    # --------------------------------------------------------

    if not found_charge:
        return None

    return round(
        total,
        2,
    )


def normalize_invoice(
    raw: dict,
) -> dict:
    """
    Convert multimodal extraction output into the
    canonical Innov8X invoice representation.

    The audit engine consumes this canonical representation,
    regardless of the original invoice layout.

    Missing values remain None.
    Unknown charges are preserved.
    No values are invented.
    """

    if not isinstance(raw, dict):

        raise TypeError(
            "Invoice must be a dictionary."
        )

    # --------------------------------------------------------
    # Calculate grand total ONCE.
    #
    # Important:
    # Do not overwrite this later with raw["grand_total"].
    # --------------------------------------------------------

    calculated_grand_total = calculate_grand_total(
        raw
    )

    normalized = {

        # ----------------------------------------------------
        # IDENTIFICATION
        # ----------------------------------------------------

        "invoice_number": clean_text(
            raw.get("invoice_number")
        ),

        "invoice_date": clean_text(
            raw.get("invoice_date")
        ),

        "shipment_reference": clean_text(
            raw.get("shipment_reference")
        ),

        "load_reference": clean_text(
            raw.get("load_reference")
        ),

        "customer_id": clean_text(
            raw.get("customer_id")
        ),

        "po_number": clean_text(
            raw.get("po_number")
        ),

        "bol_number": clean_text(
            raw.get("bol_number")
        ),

        "operator_name": clean_text(
            raw.get("operator_name")
        ),

        "truck_number": clean_text(
            raw.get("truck_number")
        ),

        # ----------------------------------------------------
        # GRAND TOTAL
        #
        # FIX:
        # Use calculated_grand_total.
        # Do NOT overwrite it with raw["grand_total"].
        # ----------------------------------------------------

        "grand_total": calculated_grand_total,

        # ----------------------------------------------------
        # LOCATIONS
        # ----------------------------------------------------

        "pickup_address": clean_text(
            raw.get("pickup_address")
        ),

        "pickup_contact": clean_text(
            raw.get("pickup_contact")
        ),

        "destination_address": clean_text(
            raw.get("destination_address")
        ),

        "destination_contact": clean_text(
            raw.get("destination_contact")
        ),

        # ----------------------------------------------------
        # DISTANCE
        # ----------------------------------------------------

        "loaded_mileage_start": clean_number(
            raw.get("loaded_mileage_start")
        ),

        "loaded_mileage_end": clean_number(
            raw.get("loaded_mileage_end")
        ),

        "loaded_mileage_total": clean_number(
            raw.get("loaded_mileage_total")
        ),

        "empty_mileage_start": clean_number(
            raw.get("empty_mileage_start")
        ),

        "empty_mileage_end": clean_number(
            raw.get("empty_mileage_end")
        ),

        "empty_mileage_total": clean_number(
            raw.get("empty_mileage_total")
        ),

        # ----------------------------------------------------
        # CHARGES
        # ----------------------------------------------------

        "transportation_charge": clean_number(
            raw.get("transportation_charge")
        ),

        "fuel_charge": clean_number(
            raw.get("fuel_charge")
        ),

        "accessorial_charge": clean_number(
            raw.get("accessorial_charge")
        ),

        "detention_charge": clean_number(
            raw.get("detention_charge")
        ),

        "permits_charge": clean_number(
            raw.get("permits_charge")
        ),

        "escorts_charge": clean_number(
            raw.get("escorts_charge")
        ),

        "special_handling_charge": clean_number(
            raw.get("special_handling_charge")
        ),

        # ----------------------------------------------------
        # CURRENCY
        # ----------------------------------------------------

        "currency": clean_text(
            raw.get("currency")
        ),

        # ----------------------------------------------------
        # UNKNOWN / EXTRA CHARGES
        # ----------------------------------------------------

        "additional_charges": (
            normalize_additional_charges(
                raw.get("additional_charges")
            )
        ),

        # ----------------------------------------------------
        # EXTRACTION METADATA
        # ----------------------------------------------------

        "extraction_metadata": (
            normalize_extraction_metadata(
                raw.get("extraction_metadata")
            )
        ),
    }

    return normalized


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    raw_ocr = {

        "invoice_number": "INV-TEST-001",

        "invoice_date": "2026-08-17",

        "shipment_reference": "SHP-123",

        "load_reference": "LOAD-456",

        "customer_id": "CUSTOMER-001",

        "transportation_charge": "$4,500.00",

        "fuel_charge": "$500.00",

        "additional_charges": [

            {
                "description": "Lumper Fee",
                "amount": "$125.00",
                "normalized_type": "accessorial",
            },

            {
                "description": "Scale Fee",
                "amount": "$25.00",
                "normalized_type": "unknown",
            },

        ],

        "grand_total": "$5,150.00",

        "currency": "USD",

        "extraction_metadata": {

            "document_type": "freight_invoice",

            "confidence": 0.94,

            "classifier_confidence": 0.97,

            "classifier_reason": (
                "Freight billing information detected."
            ),

            "needs_review": False,
        },
    }

    normalized = normalize_invoice(
        raw_ocr
    )

    print(
        json.dumps(
            normalized,
            indent=2,
        )
    )