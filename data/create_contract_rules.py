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

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "contract_rules.csv"
)


# ============================================================
# 2. LOAD SHIPMENT MASTER
# ============================================================

print("Loading shipment master...")

shipments = pd.read_csv(SHIPMENTS_FILE)


# ============================================================
# 3. BUILD SOURCE-DERIVED CONTRACT RULES
# ============================================================

print("Building source-derived contract rules...")

rules = (
    shipments[
        [
            "route_id",
            "base_rate_per_mile",
            "fuel_surcharge_rate"
        ]
    ]
    .drop_duplicates(subset="route_id")
    .copy()
)


# ============================================================
# 4. ADD CONTRACT POLICY PARAMETERS
# ============================================================
#
# IMPORTANT:
# These values are NOT claimed to come from the original
# datasets. They are explicit synthetic contract assumptions
# used because the source data does not contain these rules.
#
# They will later allow us to deliberately create invoice
# violations for the audit engine.
# ============================================================

rules["detention_free_minutes"] = 120

rules["detention_rate_per_hour"] = 50.00

rules["minimum_charge"] = 250.00


# ============================================================
# 5. RULE METADATA
# ============================================================

rules["rate_source"] = "routes.csv"

rules["detention_rule_source"] = "synthetic_contract_policy"

rules["minimum_charge_source"] = "synthetic_contract_policy"

rules["contract_version"] = "SYNTH-2026.1"


# ============================================================
# 6. CREATE CONTRACT IDs
# ============================================================

rules.insert(
    0,
    "contract_id",
    [
        f"CONTRACT{i:05d}"
        for i in range(1, len(rules) + 1)
    ]
)


# ============================================================
# 7. REORDER COLUMNS
# ============================================================

rules = rules[
    [
        "contract_id",
        "route_id",

        "contract_version",

        # SOURCE-DERIVED
        "base_rate_per_mile",
        "fuel_surcharge_rate",

        # SYNTHETIC POLICY
        "detention_free_minutes",
        "detention_rate_per_hour",
        "minimum_charge",

        # PROVENANCE
        "rate_source",
        "detention_rule_source",
        "minimum_charge_source"
    ]
]


# ============================================================
# 8. VALIDATION
# ============================================================

print("\nRunning validation...")

print(
    "Number of contract rules:",
    len(rules)
)

print(
    "Unique routes:",
    rules["route_id"].nunique()
)

print(
    "Duplicate routes:",
    rules["route_id"].duplicated().sum()
)

print(
    "Missing base rates:",
    rules["base_rate_per_mile"].isna().sum()
)

print(
    "Missing fuel surcharge rates:",
    rules["fuel_surcharge_rate"].isna().sum()
)


# ============================================================
# 9. SAVE
# ============================================================

rules.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 10. FINAL OUTPUT
# ============================================================

print("\n======================================")
print("CONTRACT RULES CREATED SUCCESSFULLY")
print("======================================")

print(
    f"File: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(rules):,}"
)

print(
    f"Columns: {len(rules.columns)}"
)

print("\nFirst 5 rules:")

print(
    rules.head().to_string(index=False)
)