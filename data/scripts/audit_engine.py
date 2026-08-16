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