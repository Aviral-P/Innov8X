import json
import re
from typing import Any


# ============================================================
# VALUE NORMALIZATION
# ============================================================

def clean_number(value: Any) -> float | None:
    """
    Convert OCR numeric output into a clean float.

    Examples:
        "4,500.00" -> 4500.0
        "$4,500.00" -> 4500.0
        4500 -> 4500.0
        None -> None
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if not value:
        return None

    # Remove currency symbols, commas and whitespace.
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
# CANONICAL INVOICE NORMALIZATION
# ============================================================

def normalize_invoice(raw: dict) -> dict:
    """
    Convert raw GLM-OCR output into the canonical
    Innov8X invoice schema.

    Missing values remain None.
    No values are invented.
    """

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

        "permits_charge": clean_number(
            raw.get("permits_charge")
        ),

        "escorts_charge": clean_number(
            raw.get("escorts_charge")
        ),

        "special_handling_charge": clean_number(
            raw.get("special_handling_charge")
        ),

        "grand_total": clean_number(
            raw.get("grand_total")
        ),

        "currency": clean_text(
            raw.get("currency")
        ),
        
        "accessorial_charge": clean_number(
            raw.get("accessorial_charge")
        ),

        "detention_charge": clean_number(
            raw.get("detention_charge")
),
    }

    return normalized


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    raw_ocr = {
        "invoice_number": "",
        "invoice_date": "",
        "po_number": "4567",
        "bol_number": "89011",
        "operator_name": "John Smith",
        "truck_number": "567",
        "pickup_address": (
            "1627 Sample St. Seattle, WA 98765"
        ),
        "pickup_contact": "Mark Johnson",
        "destination_address": (
            "1627 Sample St. Seattle, WA 98765"
        ),
        "destination_contact": "Jane Doe",
        "loaded_mileage_start": "12,345.00",
        "loaded_mileage_end": "13,000.00",
        "loaded_mileage_total": "655.00",
        "empty_mileage_start": "12,300.00",
        "empty_mileage_end": "12,345.00",
        "empty_mileage_total": "45.00",
        "transportation_charge": "4,500.00",
        "fuel_charge": "100.00",
        "permits_charge": "200.00",
        "escorts_charge": "500.00",
        "special_handling_charge": "350.00",
        "grand_total": "5,650.00",
        "currency": "USD",
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