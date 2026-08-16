import pandas as pd

inv = pd.read_csv("raw/invoices_with_errors.csv")
loads = pd.read_csv("processed/load_evidence.csv")

# ---------------------------------------------------------
# Select accessorial-error invoices
# ---------------------------------------------------------

x = inv[
    inv["injected_error_type"] == "accessorial_error"
].copy()

print("Accessorial-error invoices:", len(x))

# ---------------------------------------------------------
# Connect invoice to load evidence
# ---------------------------------------------------------

x = x.merge(
    loads[
        [
            "load_id",
            "accessorial_charges",
        ]
    ],
    on="load_id",
    how="left",
    suffixes=("_invoice", "_load"),
)

# ---------------------------------------------------------
# Calculate discrepancy
# ---------------------------------------------------------

x["accessorial_difference"] = (
    x["calculated_accessorial_charges"]
    - x["accessorial_charges"]
)

# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print("\n==============================")
print("ACCESSORIAL VALIDATION")
print("==============================")

print(
    "Missing load evidence:",
    x["accessorial_charges"].isna().sum()
)

print(
    "Charge mismatches:",
    (
        x["accessorial_difference"].abs()
        > 0.01
    ).sum()
)

print(
    "Average difference:",
    round(
        x["accessorial_difference"].mean(),
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
            "accessorial_charges",
            "calculated_accessorial_charges",
            "accessorial_difference",
            "injected_error_amount",
        ]
    ]
    .head(10)
    .to_string(index=False)
)