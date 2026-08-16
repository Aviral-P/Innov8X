import pandas as pd

print("Loading files...")

inv = pd.read_csv("processed/invoices.csv")
gt = pd.read_csv("ground_truth/audit_ground_truth.csv")
sh = pd.read_csv("processed/shipment_evidence.csv")
rates = pd.read_csv("processed/contract_rates.csv")
de = pd.read_csv("processed/delivery_evidence.csv")

print("\n--- ORIGINAL COLUMNS ---")
print("Invoice:", inv.columns.tolist())
print("Ground truth:", gt.columns.tolist())
print("Shipment:", sh.columns.tolist())
print("Rates:", rates.columns.tolist())
print("Delivery:", de.columns.tolist())

print("\n--- CLEAN INVOICES ---")

x = inv.merge(
    gt[["invoice_id", "has_injected_error"]],
    on="invoice_id",
    how="inner"
)

x = x[x["has_injected_error"] == False].copy()

print("Clean invoices:", len(x))

print("\n--- MERGE SHIPMENT EVIDENCE ---")

x = x.merge(
    sh[
        [
            "shipment_id",
            "load_id",
            "trip_id",
            "actual_distance_miles",
            "detention_minutes",
        ]
    ],
    on="shipment_id",
    how="left",
    suffixes=("_invoice", "_shipment"),
)

print("Columns after shipment merge:")
print(x.columns.tolist())

print("\n--- MERGE RATE EVIDENCE ---")

x = x.merge(
    rates[
        [
            "contract_id",
            "route_id",
            "contract_rate_per_mile",
            "contract_fuel_surcharge_rate",
        ]
    ],
    on=["contract_id", "route_id"],
    how="left",
)

print("Columns after rate merge:")
print(x.columns.tolist())

print("\n--- MERGE DELIVERY EVIDENCE ---")

de2 = de[
    [
        "load_id",
        "trip_id",
        "detention_minutes",
    ]
].rename(
    columns={
        "detention_minutes": "delivery_detention_minutes"
    }
)

x = x.merge(
    de2,
    left_on=["load_id_invoice", "trip_id"],
    right_on=["load_id", "trip_id"],
    how="left",
)

print("Columns after delivery merge:")
print(x.columns.tolist())

print("\n--- FINAL VALIDATION ---")

print(
    "Distance mismatches:",
    (
        x["actual_distance_miles_invoice"]
        != x["actual_distance_miles_shipment"]
    ).sum(),
)

print(
    "Rate mismatches:",
    (
        x["base_rate_per_mile"]
        != x["contract_rate_per_mile"]
    ).sum(),
)

print(
    "Fuel rate mismatches:",
    (
        x["fuel_surcharge_rate"]
        != x["contract_fuel_surcharge_rate"]
    ).sum(),
)

print(
    "Detention mismatches:",
    (
        x["detention_minutes_invoice"]
        != x["delivery_detention_minutes"]
    ).sum(),
)

