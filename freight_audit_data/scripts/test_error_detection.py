import pandas as pd

inv = pd.read_csv("raw/invoices_with_errors.csv")
gt = pd.read_csv("ground_truth/audit_ground_truth.csv")
rates = pd.read_csv("processed/contract_rates.csv")
sh = pd.read_csv("processed/shipment_evidence.csv")
de = pd.read_csv("processed/delivery_evidence.csv")

# Ground truth is already present in invoices_with_errors.csv.
# Use the original invoice file as the source of truth.

x = inv[
    inv["has_injected_error"] == True
].copy()

print("Errored invoices:", len(x))

# ---------------------------------------------------------
# SHIPMENT EVIDENCE
# ---------------------------------------------------------

x = x.merge(
    sh[
        [
            "shipment_id",
            "load_id",
            "trip_id",
            "actual_distance_miles"
        ]
    ],
    on="shipment_id",
    how="left",
    suffixes=("_invoice", "_shipment")
)

# ---------------------------------------------------------
# CONTRACT EVIDENCE
# ---------------------------------------------------------

x = x.merge(
    rates[
        [
            "contract_id",
            "route_id",
            "contract_rate_per_mile",
            "contract_fuel_surcharge_rate"
        ]
    ],
    on=["contract_id", "route_id"],
    how="left"
)

# ---------------------------------------------------------
# EXPECTED CHARGES FROM EVIDENCE
# ---------------------------------------------------------

x["evidence_base_charge"] = (
    x["actual_distance_miles_shipment"]
    * x["contract_rate_per_mile"]
)

x["evidence_fuel_charge"] = (
    x["actual_distance_miles_shipment"]
    * x["contract_fuel_surcharge_rate"]
)

# ---------------------------------------------------------
# ERROR DETECTION
# ---------------------------------------------------------

x["base_charge_difference"] = (
    x["calculated_base_charge"]
    - x["evidence_base_charge"]
)

x["fuel_charge_difference"] = (
    x["calculated_fuel_surcharge"]
    - x["evidence_fuel_charge"]
)

x["distance_difference"] = (
    x["actual_distance_miles_invoice"]
    - x["actual_distance_miles_shipment"]
)

# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

print("\n==============================")
print("ERROR DETECTION TEST")
print("==============================")

for error_type in sorted(
    x["injected_error_type"].unique()
):

    subset = x[
        x["injected_error_type"] == error_type
    ]

    print("\n", error_type)
    print("------------------------------")
    print("Invoices:", len(subset))

    if error_type == "distance_error":

        print(
            "Distance mismatches:",
            (
                subset["distance_difference"].abs() > 0.01
            ).sum()
        )

    elif error_type == "rate_error":

        print(
            "Base charge mismatches:",
            (
                subset["base_charge_difference"].abs() > 0.01
            ).sum()
        )

    elif error_type == "fuel_surcharge_error":

        print(
            "Fuel charge mismatches:",
            (
                subset["fuel_charge_difference"].abs() > 0.01
            ).sum()
        )

    else:

        print(
            "Average injected error:",
            round(
                subset["injected_error_amount"].mean(),
                2
            )
        )

# ---------------------------------------------------------
# SAMPLE
# ---------------------------------------------------------

print("\n==============================")
print("SAMPLE RATE ERRORS")
print("==============================")

print(
    x[
        x["injected_error_type"] == "rate_error"
    ][
        [
            "invoice_id",
            "actual_distance_miles_invoice",
            "contract_rate_per_mile",
            "calculated_base_charge",
            "evidence_base_charge",
            "base_charge_difference",
            "injected_error_amount"
        ]
    ].head(10).to_string(index=False)
)

print("\n==============================")
print("SAMPLE FUEL ERRORS")
print("==============================")

print(
    x[
        x["injected_error_type"]
        == "fuel_surcharge_error"
    ][
        [
            "invoice_id",
            "contract_fuel_surcharge_rate",
            "calculated_fuel_surcharge",
            "evidence_fuel_charge",
            "fuel_charge_difference",
            "injected_error_amount"
        ]
    ].head(10).to_string(index=False)
)
