import pandas as pd
import os


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SHIPMENTS_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "shipments.csv"
)

CONTRACTS_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "contract_rules.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "invoices.csv"
)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("Loading shipment data...")
shipments = pd.read_csv(SHIPMENTS_FILE)

print("Loading contract rules...")
contracts = pd.read_csv(CONTRACTS_FILE)


# ============================================================
# 3. MERGE SHIPMENTS WITH CONTRACT RULES
# ============================================================

print("Applying contract rules...")

invoice_data = shipments.merge(
    contracts[
        [
            "contract_id",
            "route_id",
            "base_rate_per_mile",
            "fuel_surcharge_rate",
            "detention_free_minutes",
            "detention_rate_per_hour",
            "minimum_charge"
        ]
    ],
    on="route_id",
    how="left",
    suffixes=("", "_contract")
)


# ============================================================
# 4. CALCULATE BASE FREIGHT CHARGE
# ============================================================

print("Calculating freight charges...")

invoice_data["calculated_base_charge"] = (
    invoice_data["actual_distance_miles"]
    * invoice_data["base_rate_per_mile_contract"]
)


# ============================================================
# 5. CALCULATE FUEL SURCHARGE
# ============================================================

invoice_data["calculated_fuel_surcharge"] = (
    invoice_data["actual_distance_miles"]
    * invoice_data["fuel_surcharge_rate_contract"]
)


# ============================================================
# 6. CALCULATE DETENTION
# ============================================================

invoice_data["excess_detention_minutes"] = (
    invoice_data["detention_minutes"]
    - invoice_data["detention_free_minutes"]
).clip(lower=0)


invoice_data["calculated_detention_charge"] = (
    invoice_data["excess_detention_minutes"]
    / 60
    * invoice_data["detention_rate_per_hour"]
)


# ============================================================
# 7. ACCESSORIAL CHARGES
# ============================================================

# The original dataset contains historical accessorial charges.
# We preserve them as the baseline accessorial amount.

invoice_data["calculated_accessorial_charges"] = (
    invoice_data["accessorial_charges"]
    .fillna(0)
)


# ============================================================
# 8. CALCULATE TOTAL EXPECTED CHARGE
# ============================================================

invoice_data["calculated_subtotal"] = (
    invoice_data["calculated_base_charge"]
    + invoice_data["calculated_fuel_surcharge"]
    + invoice_data["calculated_detention_charge"]
    + invoice_data["calculated_accessorial_charges"]
)


# ============================================================
# 9. APPLY MINIMUM CHARGE
# ============================================================

invoice_data["expected_total"] = (
    invoice_data[
        [
            "calculated_subtotal",
            "minimum_charge"
        ]
    ].max(axis=1)
)


# ============================================================
# 10. CREATE INVOICE IDs
# ============================================================

invoice_data.insert(
    0,
    "invoice_id",
    [
        f"INV{i:08d}"
        for i in range(1, len(invoice_data) + 1)
    ]
)


# ============================================================
# 11. CREATE INVOICE DATE
# ============================================================

invoice_data["invoice_date"] = pd.to_datetime(
    invoice_data["load_date"],
    errors="coerce"
) + pd.Timedelta(days=1)


# ============================================================
# 12. BUILD FINAL INVOICE DATASET
# ============================================================

invoices = invoice_data[
    [
        "invoice_id",
        "shipment_id",
        "load_id",
        "customer_id",
        "route_id",
        "contract_id",

        "invoice_date",

        "actual_distance_miles",
        "base_rate_per_mile_contract",
        "calculated_base_charge",

        "fuel_surcharge_rate_contract",
        "calculated_fuel_surcharge",

        "detention_minutes",
        "detention_free_minutes",
        "detention_rate_per_hour",
        "calculated_detention_charge",

        "calculated_accessorial_charges",

        "calculated_subtotal",
        "minimum_charge",
        "expected_total"
    ]
].copy()


# ============================================================
# 13. RENAME COLUMNS
# ============================================================

invoices = invoices.rename(
    columns={
        "base_rate_per_mile_contract": "base_rate_per_mile",
        "fuel_surcharge_rate_contract": "fuel_surcharge_rate"
    }
)


# ============================================================
# 14. ROUND MONETARY VALUES
# ============================================================

money_columns = [
    "base_rate_per_mile",
    "fuel_surcharge_rate",
    "calculated_base_charge",
    "calculated_fuel_surcharge",
    "detention_rate_per_hour",
    "calculated_detention_charge",
    "calculated_accessorial_charges",
    "calculated_subtotal",
    "minimum_charge",
    "expected_total"
]

for column in money_columns:
    invoices[column] = invoices[column].round(2)


# ============================================================
# 15. VALIDATION
# ============================================================

print("\nRunning validation...")

print(
    "Number of invoices:",
    len(invoices)
)

print(
    "Number of columns:",
    len(invoices.columns)
)

print(
    "Missing contract IDs:",
    invoices["contract_id"].isna().sum()
)

print(
    "Missing expected totals:",
    invoices["expected_total"].isna().sum()
)

print(
    "Minimum charge applied:",
    (
        invoices["expected_total"]
        == invoices["minimum_charge"]
    ).sum()
)


# ============================================================
# 16. SAVE
# ============================================================

invoices.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 17. FINAL OUTPUT
# ============================================================

print("\n======================================")
print("FREIGHT INVOICES CREATED SUCCESSFULLY")
print("======================================")

print(
    f"File: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(invoices):,}"
)

print(
    f"Columns: {len(invoices.columns)}"
)

print("\nFirst 5 invoices:")

print(
    invoices.head().to_string(index=False)
)