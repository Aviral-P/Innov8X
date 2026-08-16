import pandas as pd


DATA_DIR = "data/processed"


def load_data():
    print("Loading audit data...")

    invoices = pd.read_csv(
        f"{DATA_DIR}/invoices.csv"
    )

    contracts = pd.read_csv(
        f"{DATA_DIR}/contract_rates.csv"
    )

    shipments = pd.read_csv(
        f"{DATA_DIR}/shipment_evidence.csv"
    )

    deliveries = pd.read_csv(
        f"{DATA_DIR}/delivery_evidence.csv"
    )

    loads = pd.read_csv(
        f"{DATA_DIR}/load_evidence.csv"
    )

    print(f"Invoices:   {len(invoices):,}")
    print(f"Contracts:  {len(contracts):,}")
    print(f"Shipments:  {len(shipments):,}")
    print(f"Deliveries: {len(deliveries):,}")
    print(f"Loads:      {len(loads):,}")

    return (
        invoices,
        contracts,
        shipments,
        deliveries,
        loads,
    )


def audit_distance(invoices, shipments):

    print("\nRunning distance audit...")

    x = invoices.merge(
        shipments[
            [
                "shipment_id",
                "actual_distance_miles",
            ]
        ],
        on="shipment_id",
        how="left",
        suffixes=(
            "_invoice",
            "_shipment",
        ),
    )

    x["distance_difference"] = (
        x["actual_distance_miles_invoice"]
        - x["actual_distance_miles_shipment"]
    )

    x["distance_error"] = (
        x["distance_difference"].abs()
        > 0.01
    )

    flagged = x["distance_error"].sum()

    print(
        f"Distance discrepancies: {flagged:,}"
    )

    return x

    
def audit_rate(invoices, shipments, contracts):

    print("\nRunning rate audit...")

    x = invoices.merge(
        shipments[
            [
                "shipment_id",
                "actual_distance_miles",
            ]
        ],
        on="shipment_id",
        how="left",
        suffixes=(
            "_invoice",
            "_shipment",
        ),
    )

    x = x.merge(
        contracts[
            [
                "contract_id",
                "route_id",
                "contract_rate_per_mile",
            ]
        ],
        on=[
            "contract_id",
            "route_id",
        ],
        how="left",
    )

    x["evidence_base_charge"] = (
        x["actual_distance_miles_invoice"]
        * x["contract_rate_per_mile"]
    )

    x["base_charge_difference"] = (
        x["calculated_base_charge"]
        - x["evidence_base_charge"]
    )

    x["rate_error"] = (
        x["base_charge_difference"].abs()
        > 0.01
    )

    flagged = x["rate_error"].sum()

    print(
        f"Rate discrepancies: {flagged:,}"
    )

    return x

def audit_fuel_surcharge(invoices, contracts):

    print("\nRunning fuel surcharge audit...")

    x = invoices.merge(
        contracts[
            [
                "contract_id",
                "route_id",
                "contract_fuel_surcharge_rate",
            ]
        ],
        on=[
            "contract_id",
            "route_id",
        ],
        how="left",
    )

    x["evidence_fuel_charge"] = (
        x["actual_distance_miles"]
        * x["contract_fuel_surcharge_rate"]
    )

    x["fuel_charge_difference"] = (
        x["calculated_fuel_surcharge"]
        - x["evidence_fuel_charge"]
    )

    x["fuel_surcharge_error"] = (
        x["fuel_charge_difference"].abs()
        > 0.01
    )

    flagged = x["fuel_surcharge_error"].sum()

    print(
        f"Fuel surcharge discrepancies: {flagged:,}"
    )

    return x

def audit_detention(invoices, shipments, deliveries):

    print("\nRunning detention audit...")

    x = invoices.merge(
        shipments[
            [
                "shipment_id",
                "load_id",
                "trip_id",
            ]
        ],
        on="shipment_id",
        how="left",
        suffixes=(
            "_invoice",
            "_shipment",
        ),
    )

    delivery = deliveries[
        [
            "load_id",
            "trip_id",
            "detention_minutes",
        ]
    ].rename(
        columns={
            "detention_minutes":
            "delivery_detention_minutes"
        }
    )

    x = x.merge(
        delivery,
        left_on=[
            "load_id_invoice",
            "trip_id",
        ],
        right_on=[
            "load_id",
            "trip_id",
        ],
        how="left",
    )

    x["billable_detention_minutes"] = (
        x["delivery_detention_minutes"]
        - x["detention_free_minutes"]
    ).clip(lower=0)

    x["evidence_detention_charge"] = (
        x["billable_detention_minutes"]
        / 60
        * x["detention_rate_per_hour"]
    )

    x["detention_charge_difference"] = (
        x["calculated_detention_charge"]
        - x["evidence_detention_charge"]
    )

    x["detention_error"] = (
        x["detention_charge_difference"].abs()
        > 0.01
    )

    flagged = x["detention_error"].sum()

    print(
        f"Detention discrepancies: {flagged:,}"
    )

    return x

def audit_accessorial(invoices, loads):

    print("\nRunning accessorial audit...")

    x = invoices.merge(
        loads[
            [
                "load_id",
                "accessorial_charges",
            ]
        ],
        on="load_id",
        how="left",
        suffixes=(
            "_invoice",
            "_load",
        ),
    )

    x["accessorial_difference"] = (
        x["calculated_accessorial_charges"]
        - x["accessorial_charges"]
    )

    x["accessorial_error"] = (
        x["accessorial_difference"].abs()
        > 0.01
    )

    flagged = x["accessorial_error"].sum()

    print(
        f"Accessorial discrepancies: {flagged:,}"
    )

    return x

if __name__ == "__main__":

    (
        invoices,
        contracts,
        shipments,
        deliveries,
        loads,
    ) = load_data()

    audit_distance(
        invoices,
        shipments,
    )

    audit_rate(
        invoices,
        shipments,
        contracts,
    )
    
    audit_fuel_surcharge(
        invoices,
        contracts,
    )
    
    audit_detention(
        invoices,
        shipments,
        deliveries,
    )
    
    audit_accessorial(
        invoices,
        loads,
    )