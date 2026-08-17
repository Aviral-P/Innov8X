import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCHED_INVOICE_PATH = (
    PROJECT_ROOT
    / "data"
    / "matched_invoice.json"
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
    / "invoice_audit_result.json"
)


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=None):
    """
    Convert a value to float without crashing on null,
    empty strings, NaN, or invalid values.
    """

    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def money(value):
    value = safe_float(value)

    if value is None:
        return None

    return round(value, 2)


def assign_severity(overcharge_amount):
    """
    Assign audit severity based on overcharge exposure.
    """

    amount = safe_float(
        overcharge_amount,
        0.0,
    )

    if amount >= 1000:
        return "CRITICAL"

    if amount >= 500:
        return "HIGH"

    if amount >= 100:
        return "MEDIUM"

    return "LOW"


def load_data():

    with open(
        MATCHED_INVOICE_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        matched = json.load(f)

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
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    )


def first_valid_number(
    invoice,
    fields,
):
    """
    Return the first usable numeric invoice value.
    """

    for field in fields:

        value = safe_float(
            invoice.get(field)
        )

        if value is not None:
            return value

    return None


def calculate_billed_total(invoice):
    """
    Use the printed invoice grand total when available.

    If the grand total is missing or unreadable, reconstruct
    the billed total from explicitly extracted charge fields.

    This reconstruction is used internally for auditing and
    is never presented as the invoice's printed total.
    """

    grand_total = safe_float(
        invoice.get("grand_total")
    )

    if grand_total is not None:
        return round(grand_total, 2)

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
    found_component = False

    for field in charge_fields:

        value = safe_float(
            invoice.get(field)
        )

        if value is not None:
            total += value
            found_component = True

    if not found_component:
        return None

    return round(total, 2)


def review_result(
    invoice,
    matching,
    reason,
    checks=None,
):
    """
    Return a safe REVIEW result instead of crashing when
    evidence or invoice fields are insufficient for a
    deterministic financial decision.
    """

    return {
        "invoice_id": invoice.get(
            "invoice_number"
        ),

        "shipment_id": matching.get(
            "shipment_id"
        ),

        "load_id": matching.get(
            "load_id"
        ),

        "contract_id": matching.get(
            "contract_id"
        ),

        "audit_status": "REVIEW",

        "error_types": [],

        "overcharge_amount": 0.0,

        "severity": "LOW",

        "billed_total": calculate_billed_total(
            invoice
        ),

        "expected_total": None,

        "total_variance": None,

        "review_reason": reason,

        "checks": checks or {},

        "evidence": {
            "shipment_source": "shipment_evidence.csv",
            "load_source": "load_evidence.csv",
            "delivery_source": "delivery_evidence.csv",
            "contract_source": "contract_rates.csv",
        },
    }


# ============================================================
# AUDIT
# ============================================================

def audit_invoice(
    matched,
    invoices,
    shipments,
    loads,
    deliveries,
    contracts,
):

    invoice = matched["invoice"]

    matching = matched["matching"]

    if matching.get("match_status") != "MATCHED":

        raise RuntimeError(
            "Invoice must be successfully matched "
            "before auditing."
        )

    shipment_id = matching.get(
        "shipment_id"
    )

    load_id = matching.get(
        "load_id"
    )

    route_id = matching.get(
        "route_id"
    )

    if not shipment_id or not load_id or not route_id:

        return review_result(
            invoice,
            matching,
            "Matched record does not contain the "
            "shipment, load, or route evidence required "
            "for a deterministic audit.",
        )

    # --------------------------------------------------------
    # FIND EVIDENCE
    # --------------------------------------------------------

    shipment = shipments[
        shipments["shipment_id"].astype(str)
        == str(shipment_id)
    ]

    load = loads[
        loads["load_id"].astype(str)
        == str(load_id)
    ]

    delivery = deliveries[
        deliveries["load_id"].astype(str)
        == str(load_id)
    ]

    contract = contracts[
        contracts["route_id"].astype(str)
        == str(route_id)
    ]

    invoice_number = invoice.get(
        "invoice_number"
    )

    invoice_record = invoices[
        invoices["invoice_id"].astype(str)
        == str(invoice_number)
    ]

    if len(shipment) != 1:

        return review_result(
            invoice,
            matching,
            f"Expected one shipment evidence record, "
            f"found {len(shipment)}.",
        )

    if len(load) != 1:

        return review_result(
            invoice,
            matching,
            f"Expected one load evidence record, "
            f"found {len(load)}.",
        )

    if len(delivery) != 1:

        return review_result(
            invoice,
            matching,
            f"Expected one delivery event, "
            f"found {len(delivery)}.",
        )

    if len(contract) == 0:

        return review_result(
            invoice,
            matching,
            f"No contract found for route {route_id}.",
        )

    shipment = shipment.iloc[0]
    load = load.iloc[0]
    delivery = delivery.iloc[0]

    # --------------------------------------------------------
    # CONTRACT VALIDITY
    # --------------------------------------------------------

    invoice_date = pd.to_datetime(
        invoice.get("invoice_date"),
        errors="coerce",
    )

    if pd.isna(invoice_date):

        return review_result(
            invoice,
            matching,
            "Invoice date is missing or unreadable; "
            "the active contract cannot be determined.",
        )

    contract = contract.copy()

    contract["valid_from"] = pd.to_datetime(
        contract["valid_from"],
        errors="coerce",
    )

    contract["valid_to"] = pd.to_datetime(
        contract["valid_to"],
        errors="coerce",
    )

    valid_contracts = contract[
        (contract["valid_from"] <= invoice_date)
        & (contract["valid_to"] >= invoice_date)
    ]

    if len(valid_contracts) == 0:

        return review_result(
            invoice,
            matching,
            "No contract was valid on the invoice date.",
        )

    if len(valid_contracts) > 1:

        return review_result(
            invoice,
            matching,
            "Multiple contracts were valid on the "
            "invoice date; automatic auditing is unsafe.",
        )

    contract = valid_contracts.iloc[0]

    # --------------------------------------------------------
    # EVIDENCE VALUES
    # --------------------------------------------------------

    actual_distance = safe_float(
        shipment.get("actual_distance_miles")
    )

    contract_rate = safe_float(
        contract.get("contract_rate_per_mile")
    )

    contract_fuel_rate = safe_float(
        contract.get(
            "contract_fuel_surcharge_rate"
        )
    )

    billed_transportation = first_valid_number(
        invoice,
        [
            "transportation_charge",
        ],
    )

    billed_fuel = first_valid_number(
        invoice,
        [
            "fuel_charge",
        ],
    )

    billed_accessorial = first_valid_number(
        invoice,
        [
            "accessorial_charge",
        ],
    )

    billed_detention = first_valid_number(
        invoice,
        [
            "detention_charge",
        ],
    )

    if billed_accessorial is None:
        billed_accessorial = 0.0

    if billed_detention is None:
        billed_detention = 0.0

    billed_total = calculate_billed_total(
        invoice
    )

    # --------------------------------------------------------
    # REQUIRED VALUES FOR RATE/FUEL AUDIT
    # --------------------------------------------------------

    missing = []

    if actual_distance is None:
        missing.append(
            "actual_distance_miles"
        )

    if contract_rate is None:
        missing.append(
            "contract_rate_per_mile"
        )

    if billed_transportation is None:
        missing.append(
            "transportation_charge"
        )

    if contract_fuel_rate is None:
        missing.append(
            "contract_fuel_surcharge_rate"
        )

    if billed_fuel is None:
        missing.append(
            "fuel_charge"
        )

    if billed_total is None:
        missing.append(
            "invoice_total_or_charge_components"
        )

    if missing:

        return review_result(
            invoice,
            matching,
            "Insufficient numeric evidence for a "
            "deterministic financial audit.",
            {
                "status": "REVIEW",
                "missing_values": missing,
            },
        )

    # --------------------------------------------------------
    # DETENTION EVIDENCE
    # --------------------------------------------------------

    detention_minutes = safe_float(
        shipment.get("detention_minutes")
    )

    detention_free_minutes = None

    if len(invoice_record) == 1:

        detention_free_minutes = safe_float(
            invoice_record.iloc[0].get(
                "detention_free_minutes"
            )
        )

    if detention_minutes is None:

        return review_result(
            invoice,
            matching,
            "Detention evidence is missing from the "
            "operational shipment record.",
        )

    if detention_free_minutes is None:

        return review_result(
            invoice,
            matching,
            "Detention policy evidence is missing from "
            "the matched billing record.",
        )

    # --------------------------------------------------------
    # RATE AUDIT
    # --------------------------------------------------------

    expected_transportation = (
        actual_distance
        * contract_rate
    )

    transportation_variance = (
        billed_transportation
        - expected_transportation
    )

    rate_status = (
        "FAIL"
        if transportation_variance > 0.01
        else "PASS"
    )

    # --------------------------------------------------------
    # FUEL AUDIT
    # --------------------------------------------------------

    expected_fuel = (
        actual_distance
        * contract_fuel_rate
    )

    fuel_variance = (
        billed_fuel
        - expected_fuel
    )

    fuel_status = (
        "FAIL"
        if fuel_variance > 0.01
        else "PASS"
    )

    # --------------------------------------------------------
    # ACCESSORIAL AUDIT
    # --------------------------------------------------------

    expected_accessorial = safe_float(
        load.get("accessorial_charges")
    )

    if expected_accessorial is None:

        return review_result(
            invoice,
            matching,
            "Accessorial contract evidence is missing.",
        )

    accessorial_variance = (
        billed_accessorial
        - expected_accessorial
    )

    accessorial_status = (
        "FAIL"
        if accessorial_variance > 0.01
        else "PASS"
    )

    # --------------------------------------------------------
    # DETENTION AUDIT
    # --------------------------------------------------------

    if detention_minutes <= detention_free_minutes:

        expected_detention = 0.0

    else:

        excess_minutes = (
            detention_minutes
            - detention_free_minutes
        )

        detention_rate = None

        if len(invoice_record) == 1:

            detention_rate = safe_float(
                invoice_record.iloc[0].get(
                    "detention_rate_per_hour"
                )
            )

        if detention_rate is None:

            return review_result(
                invoice,
                matching,
                "Detention exceeded the free period, "
                "but no detention rate evidence is available.",
            )

        expected_detention = (
            excess_minutes / 60
        ) * detention_rate

    detention_variance = (
        billed_detention
        - expected_detention
    )

    detention_status = (
        "FAIL"
        if detention_variance > 0.01
        else "PASS"
    )

    # --------------------------------------------------------
    # TOTAL AUDIT
    # --------------------------------------------------------

    expected_total = (
        expected_transportation
        + expected_fuel
        + expected_accessorial
        + expected_detention
    )

    total_variance = (
        billed_total
        - expected_total
    )

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    failures = []

    if rate_status == "FAIL":
        failures.append(
            "rate_error"
        )

    if fuel_status == "FAIL":
        failures.append(
            "fuel_surcharge_error"
        )

    if accessorial_status == "FAIL":
        failures.append(
            "accessorial_error"
        )

    if detention_status == "FAIL":
        failures.append(
            "detention_error"
        )

    audit_status = (
        "FAIL"
        if failures
        else "PASS"
    )

    # Only positive variances represent potential
    # overcharges. Undercharges do not create exposure.

    overcharge = sum(
        max(
            0,
            value,
        )
        for value in [
            transportation_variance,
            fuel_variance,
            accessorial_variance,
            detention_variance,
        ]
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "invoice_id": invoice.get(
            "invoice_number"
        ),

        "shipment_id": shipment_id,

        "load_id": load_id,

        "contract_id": contract.get(
            "contract_id"
        ),

        "audit_status": audit_status,

        "error_types": failures,

        "overcharge_amount": money(
            overcharge
        ),

        "severity": assign_severity(
            overcharge
        ),

        "billed_total": money(
            billed_total
        ),

        "expected_total": money(
            expected_total
        ),

        "total_variance": money(
            total_variance
        ),

        "checks": {
            "rate": {
                "status": rate_status,
                "actual_distance": money(
                    actual_distance
                ),
                "contract_rate_per_mile": money(
                    contract_rate
                ),
                "expected_transportation": money(
                    expected_transportation
                ),
                "billed_transportation": money(
                    billed_transportation
                ),
                "variance": money(
                    transportation_variance
                ),
            },

            "fuel_surcharge": {
                "status": fuel_status,
                "contract_rate": money(
                    contract_fuel_rate
                ),
                "expected_fuel": money(
                    expected_fuel
                ),
                "billed_fuel": money(
                    billed_fuel
                ),
                "variance": money(
                    fuel_variance
                ),
            },

            "accessorial": {
                "status": accessorial_status,
                "expected": money(
                    expected_accessorial
                ),
                "billed": money(
                    billed_accessorial
                ),
                "variance": money(
                    accessorial_variance
                ),
            },

            "detention": {
                "status": detention_status,
                "detention_minutes": money(
                    detention_minutes
                ),
                "free_minutes": money(
                    detention_free_minutes
                ),
                "expected": money(
                    expected_detention
                ),
                "billed": money(
                    billed_detention
                ),
                "variance": money(
                    detention_variance
                ),
            },
        },

        "evidence": {
            "shipment_source": (
                "shipment_evidence.csv"
            ),
            "load_source": (
                "load_evidence.csv"
            ),
            "delivery_source": (
                "delivery_evidence.csv"
            ),
            "contract_source": (
                "contract_rates.csv"
            ),
        },
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading matched invoice and evidence..."
    )

    (
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    ) = load_data()

    print(
        "Running invoice audit..."
    )

    result = audit_invoice(
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\nAudit result:"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
