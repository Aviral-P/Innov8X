import json
from pathlib import Path

import pandas as pd

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MATCHED_INVOICE_PATH = PROJECT_ROOT / "data" / "matched_invoice.json"

INVOICES_PATH = PROJECT_ROOT / "data" / "processed" / "invoices.csv"

SHIPMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "shipment_evidence.csv"

LOADS_PATH = PROJECT_ROOT / "data" / "processed" / "load_evidence.csv"

DELIVERIES_PATH = PROJECT_ROOT / "data" / "processed" / "delivery_evidence.csv"

CONTRACTS_PATH = PROJECT_ROOT / "data" / "processed" / "contract_rates.csv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "invoice_audit_result.json"


# ============================================================
# HELPERS
# ============================================================


def money(value):
    if value is None:
        return None

    return round(float(value), 2)


def assign_severity(overcharge_amount):
    """
    Assign audit severity based on overcharge exposure.

    Uses the same severity bands as the existing
    audit engine.
    """

    if overcharge_amount >= 1000:
        return "CRITICAL"

    if overcharge_amount >= 500:
        return "HIGH"

    if overcharge_amount >= 100:
        return "MEDIUM"

    return "LOW"


def load_data():

    with open(
        MATCHED_INVOICE_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        matched = json.load(f)

    invoices = pd.read_csv(INVOICES_PATH)

    shipments = pd.read_csv(SHIPMENTS_PATH)

    loads = pd.read_csv(LOADS_PATH)

    deliveries = pd.read_csv(DELIVERIES_PATH)

    contracts = pd.read_csv(CONTRACTS_PATH)

    return (
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    )


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

    if matching["match_status"] != "MATCHED":
        raise RuntimeError("Invoice must be successfully matched " "before auditing.")

    shipment_id = matching["shipment_id"]
    load_id = matching["load_id"]
    route_id = matching["route_id"]

    # --------------------------------------------------------
    # FIND EVIDENCE
    # --------------------------------------------------------

    shipment = shipments[shipments["shipment_id"] == shipment_id]

    load = loads[loads["load_id"] == load_id]

    delivery = deliveries[deliveries["load_id"] == load_id]

    contract = contracts[contracts["route_id"] == route_id]

    invoice_record = invoices[invoices["invoice_id"] == invoice["invoice_number"]]

    if len(shipment) != 1:
        raise RuntimeError(f"Expected one shipment, found {len(shipment)}.")

    if len(load) != 1:
        raise RuntimeError(f"Expected one load, found {len(load)}.")

    if len(delivery) != 1:
        raise RuntimeError(f"Expected one delivery event, found {len(delivery)}.")

    if len(contract) == 0:
        raise RuntimeError(f"No contract found for route {route_id}.")

    shipment = shipment.iloc[0]
    load = load.iloc[0]
    delivery = delivery.iloc[0]

    # Prefer the contract active on the invoice date.
    invoice_date = pd.to_datetime(invoice["invoice_date"])

    contract = contract.copy()

    contract["valid_from"] = pd.to_datetime(contract["valid_from"])

    contract["valid_to"] = pd.to_datetime(contract["valid_to"])

    valid_contracts = contract[
        (contract["valid_from"] <= invoice_date)
        & (contract["valid_to"] >= invoice_date)
    ]

    if len(valid_contracts) == 0:
        raise RuntimeError("No contract was valid on the invoice date.")

    contract = valid_contracts.iloc[0]

    # --------------------------------------------------------
    # VALUES
    # --------------------------------------------------------

    actual_distance = float(shipment["actual_distance_miles"])

    contract_rate = float(contract["contract_rate_per_mile"])

    contract_fuel_rate = float(contract["contract_fuel_surcharge_rate"])

    billed_transportation = float(invoice["transportation_charge"])

    billed_fuel = float(invoice["fuel_charge"])

    billed_accessorial = float(invoice["accessorial_charge"] or 0)

    billed_detention = float(invoice["detention_charge"] or 0)

    billed_total = float(invoice["grand_total"])

    detention_minutes = float(shipment["detention_minutes"])

    detention_free_minutes = float(invoice_record.iloc[0]["detention_free_minutes"])

    # --------------------------------------------------------
    # RATE AUDIT
    # --------------------------------------------------------

    expected_transportation = actual_distance * contract_rate

    transportation_variance = billed_transportation - expected_transportation

    rate_status = "FAIL" if abs(transportation_variance) > 0.01 else "PASS"

    # --------------------------------------------------------
    # FUEL AUDIT
    # --------------------------------------------------------

    expected_fuel = actual_distance * contract_fuel_rate

    fuel_variance = billed_fuel - expected_fuel

    fuel_status = "FAIL" if abs(fuel_variance) > 0.01 else "PASS"

    # --------------------------------------------------------
    # ACCESSORIAL AUDIT
    # --------------------------------------------------------

    expected_accessorial = float(load["accessorial_charges"])

    accessorial_variance = billed_accessorial - expected_accessorial

    accessorial_status = "FAIL" if abs(accessorial_variance) > 0.01 else "PASS"

    # --------------------------------------------------------
    # DETENTION AUDIT
    # --------------------------------------------------------

    if detention_minutes <= detention_free_minutes:

        expected_detention = 0.0

    else:

        excess_minutes = detention_minutes - detention_free_minutes

        detention_rate = float(invoice_record.iloc[0]["detention_rate_per_hour"])

        expected_detention = (excess_minutes / 60) * detention_rate

    detention_variance = billed_detention - expected_detention

    detention_status = "FAIL" if abs(detention_variance) > 0.01 else "PASS"

    # --------------------------------------------------------
    # TOTAL AUDIT
    # --------------------------------------------------------

    expected_total = (
        expected_transportation
        + expected_fuel
        + expected_accessorial
        + expected_detention
    )

    total_variance = billed_total - expected_total

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    failures = []

    if rate_status == "FAIL":
        failures.append("rate_error")

    if fuel_status == "FAIL":
        failures.append("fuel_surcharge_error")

    if accessorial_status == "FAIL":
        failures.append("accessorial_error")

    if detention_status == "FAIL":
        failures.append("detention_error")

    audit_status = "FAIL" if failures else "PASS"

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
        "invoice_id": invoice["invoice_number"],
        "shipment_id": shipment_id,
        "load_id": load_id,
        "contract_id": contract["contract_id"],
        "audit_status": audit_status,
        "error_types": failures,
        "overcharge_amount": money(overcharge),
        "severity": assign_severity(overcharge),
        "billed_total": money(billed_total),
        "expected_total": money(expected_total),
        "total_variance": money(total_variance),
        "checks": {
            "rate": {
                "status": rate_status,
                "actual_distance": actual_distance,
                "contract_rate_per_mile": contract_rate,
                "expected_transportation": money(expected_transportation),
                "billed_transportation": money(billed_transportation),
                "variance": money(transportation_variance),
            },
            "fuel_surcharge": {
                "status": fuel_status,
                "contract_rate": contract_fuel_rate,
                "expected_fuel": money(expected_fuel),
                "billed_fuel": money(billed_fuel),
                "variance": money(fuel_variance),
            },
            "accessorial": {
                "status": accessorial_status,
                "expected": money(expected_accessorial),
                "billed": money(billed_accessorial),
                "variance": money(accessorial_variance),
            },
            "detention": {
                "status": detention_status,
                "detention_minutes": detention_minutes,
                "free_minutes": detention_free_minutes,
                "expected": money(expected_detention),
                "billed": money(billed_detention),
                "variance": money(detention_variance),
            },
        },
        "evidence": {
            "shipment_source": ("shipment_evidence.csv"),
            "load_source": ("load_evidence.csv"),
            "delivery_source": ("delivery_evidence.csv"),
            "contract_source": ("contract_rates.csv"),
        },
    }


# ============================================================
# MAIN
# ============================================================


def main():

    print("Loading matched invoice and evidence...")

    (
        matched,
        invoices,
        shipments,
        loads,
        deliveries,
        contracts,
    ) = load_data()

    print("Running invoice audit...")

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

    print("\nAudit result:")

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
