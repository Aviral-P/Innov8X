import pandas as pd
import numpy as np
import os


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "invoices.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "invoices_with_errors.csv"
)


# ============================================================
# 2. LOAD CLEAN INVOICES
# ============================================================

print("Loading clean invoices...")

invoices = pd.read_csv(INPUT_FILE)

numeric_decimal_columns = [
    "actual_distance_miles",
    "base_rate_per_mile",
    "fuel_surcharge_rate",
    "calculated_base_charge",
    "calculated_fuel_surcharge",
    "calculated_detention_charge",
    "calculated_accessorial_charges",
    "calculated_subtotal",
    "expected_total",
    "minimum_charge"
]

for column in numeric_decimal_columns:
    invoices[column] = invoices[column].astype(float)

print(
    f"Loaded {len(invoices):,} invoices."
)


# ============================================================
# 3. REPRODUCIBLE RANDOMNESS
# ============================================================

np.random.seed(42)


# ============================================================
# 4. ADD ERROR METADATA
# ============================================================

invoices["has_injected_error"] = False

invoices["injected_error_type"] = ""

invoices["injected_error_amount"] = 0.0


# ============================================================
# 5. SELECT ELIGIBLE INVOICES
# ============================================================

# We only inject errors into a subset of invoices.
# Most invoices remain completely correct.

eligible = invoices.index.to_numpy(copy=True)

np.random.shuffle(eligible)

error_count = int(len(invoices) * 0.15)

error_indices = eligible[:error_count]


# ============================================================
# 6. DEFINE ERROR TYPES
# ============================================================

error_types = [
    "rate_error",
    "fuel_surcharge_error",
    "detention_error",
    "accessorial_error",
    "distance_error"
]


# Distribute errors approximately evenly
error_assignments = np.random.choice(
    error_types,
    size=error_count
)


# ============================================================
# 7. INJECT ERRORS
# ============================================================

print("Injecting billing errors...")


for index, error_type in zip(
    error_indices,
    error_assignments
):

    expected = invoices.loc[
        index,
        "expected_total"
    ]

    error_amount = 0.0


    # --------------------------------------------------------
    # RATE ERROR
    # --------------------------------------------------------

    if error_type == "rate_error":

        # Carrier bills 10% above contracted rate

        original_base = invoices.loc[
            index,
            "calculated_base_charge"
        ]

        inflated_base = original_base * 1.10

        error_amount = inflated_base - original_base

        invoices.loc[
            index,
            "calculated_base_charge"
        ] = round(inflated_base, 2)


    # --------------------------------------------------------
    # FUEL SURCHARGE ERROR
    # --------------------------------------------------------

    elif error_type == "fuel_surcharge_error":

        original_fuel = invoices.loc[
            index,
            "calculated_fuel_surcharge"
        ]

        inflated_fuel = original_fuel * 1.20

        error_amount = inflated_fuel - original_fuel

        invoices.loc[
            index,
            "calculated_fuel_surcharge"
        ] = round(inflated_fuel, 2)


    # --------------------------------------------------------
    # DETENTION ERROR
    # --------------------------------------------------------

    elif error_type == "detention_error":

        # Add an unauthorized $100 detention charge

        error_amount = 100.00

        invoices.loc[
            index,
            "calculated_detention_charge"
        ] += error_amount


    # --------------------------------------------------------
    # ACCESSORIAL ERROR
    # --------------------------------------------------------

    elif error_type == "accessorial_error":

        # Duplicate an existing accessorial charge

        original_accessorial = invoices.loc[
            index,
            "calculated_accessorial_charges"
        ]

        if original_accessorial > 0:

            error_amount = original_accessorial

            invoices.loc[
                index,
                "calculated_accessorial_charges"
            ] = round(
                original_accessorial * 2,
                2
            )

        else:

            error_amount = 75.00

            invoices.loc[
                index,
                "calculated_accessorial_charges"
            ] = 75.00


    # --------------------------------------------------------
    # DISTANCE ERROR
    # --------------------------------------------------------

    elif error_type == "distance_error":

        # Invoice uses 15% more mileage than actual

        original_distance = invoices.loc[
            index,
            "actual_distance_miles"
        ]

        inflated_distance = (
            original_distance * 1.15
        )

        # Recalculate base and fuel charges
        base_rate = invoices.loc[
            index,
            "base_rate_per_mile"
        ]

        fuel_rate = invoices.loc[
            index,
            "fuel_surcharge_rate"
        ]

        old_total_distance_charges = (
            original_distance * base_rate
            + original_distance * fuel_rate
        )

        new_total_distance_charges = (
            inflated_distance * base_rate
            + inflated_distance * fuel_rate
        )

        error_amount = (
            new_total_distance_charges
            - old_total_distance_charges
        )

        invoices.loc[
            index,
            "actual_distance_miles"
        ] = round(
            inflated_distance,
            2
        )

        invoices.loc[
            index,
            "calculated_base_charge"
        ] = round(
            inflated_distance * base_rate,
            2
        )

        invoices.loc[
            index,
            "calculated_fuel_surcharge"
        ] = round(
            inflated_distance * fuel_rate,
            2
        )


    # ========================================================
    # RECALCULATE SUBTOTAL
    # ========================================================

    invoices.loc[
        index,
        "calculated_subtotal"
    ] = round(
        invoices.loc[
            index,
            "calculated_base_charge"
        ]
        + invoices.loc[
            index,
            "calculated_fuel_surcharge"
        ]
        + invoices.loc[
            index,
            "calculated_detention_charge"
        ]
        + invoices.loc[
            index,
            "calculated_accessorial_charges"
        ],
        2
    )


    # ========================================================
    # RECALCULATE INVOICE TOTAL
    # ========================================================

    invoices.loc[
        index,
        "expected_total"
    ] = round(
        max(
            invoices.loc[
                index,
                "calculated_subtotal"
            ],
            invoices.loc[
                index,
                "minimum_charge"
            ]
        ),
        2
    )


    # ========================================================
    # STORE ERROR METADATA
    # ========================================================

    invoices.loc[
        index,
        "has_injected_error"
    ] = True

    invoices.loc[
        index,
        "injected_error_type"
    ] = error_type

    invoices.loc[
        index,
        "injected_error_amount"
    ] = round(
        error_amount,
        2
    )


# ============================================================
# 8. CREATE BILLED AMOUNT
# ============================================================

# expected_total now represents the corrupted invoice amount
# for errored invoices.

invoices["billed_amount"] = invoices["expected_total"]


# ============================================================
# 9. SAVE
# ============================================================

invoices.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 10. VALIDATION
# ============================================================

print("\n======================================")
print("BILLING ERRORS INJECTED")
print("======================================")

print(
    f"Total invoices: {len(invoices):,}"
)

print(
    f"Invoices with errors: "
    f"{invoices['has_injected_error'].sum():,}"
)

print(
    f"Clean invoices: "
    f"{(~invoices['has_injected_error']).sum():,}"
)

print("\nError distribution:")

print(
    invoices[
        invoices["has_injected_error"]
    ]["injected_error_type"]
    .value_counts()
)


print("\nTotal injected overcharge:")

print(
    f"${invoices['injected_error_amount'].sum():,.2f}"
)


print("\nSaved to:")

print(OUTPUT_FILE)