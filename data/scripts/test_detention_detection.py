import pandas as pd

inv = pd.read_csv("raw/invoices_with_errors.csv")
sh = pd.read_csv("processed/shipment_evidence.csv")
de = pd.read_csv("processed/delivery_evidence.csv")

# ---------------------------------------------------------
# Select detention-error invoices
# ---------------------------------------------------------

x = inv[
    inv["injected_error_type"] == "detention_error"
].copy()

print("Detention-error invoices:", len(x))

# ---------------------------------------------------------
# Connect shipment/load/trip
# ---------------------------------------------------------

x = x.merge(
    sh[
        [
            "shipment_id",
            "load_id",
            "trip_id",
        ]
    ],
    on="shipment_id",
    how="left",
    suffixes=("_invoice", "_shipment"),
)

# ---------------------------------------------------------
# Connect delivery evidence
# ---------------------------------------------------------

de2 = de[
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
    de2,
    left_on=["load_id_invoice", "trip_id"],
    right_on=["load_id", "trip_id"],
    how="left",
)

# ---------------------------------------------------------
# Calculate expected detention
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print("\n==============================")
print("DETENTION VALIDATION")
print("==============================")

print(
    "Missing delivery evidence:",
    x["delivery_detention_minutes"].isna().sum()
)

print(
    "Charge mismatches:",
    (
        x["detention_charge_difference"].abs()
        > 0.01
    ).sum()
)

print(
    "Average difference:",
    round(
        x["detention_charge_difference"].mean(),
        2
    )
)

print(
    "Average injected error:",
    round(
        x["injected_error_amount"].mean(),
        2
    )
)

print("\n==============================")
print("SAMPLE")
print("==============================")

print(
    x[
        [
            "invoice_id",
            "delivery_detention_minutes",
            "detention_free_minutes",
            "billable_detention_minutes",
            "detention_rate_per_hour",
            "evidence_detention_charge",
            "calculated_detention_charge",
            "detention_charge_difference",
            "injected_error_amount",
        ]
    ]
    .head(10)
    .to_string(index=False)
)