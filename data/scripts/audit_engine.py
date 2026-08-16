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

def build_audit_results(
    invoices,
    distance_results,
    rate_results,
    fuel_results,
    detention_results,
    accessorial_results,
):

    print("\nBuilding audit results...")

    results = invoices[
        [
            "invoice_id",
            "shipment_id",
            "load_id",
            "billed_amount",
        ]
    ].copy()

    results["audit_status"] = "PASS"
    results["error_type"] = ""
    results["overcharge_amount"] = 0.0
    results["expected_amount"] = results["billed_amount"]
    results["evidence_source"] = ""
    results["actual_value"] = float("nan")
    results["expected_value"] = float("nan")
    results["explanation"] = ""

    # ---------------------------------------------------------
    # DISTANCE
    # ---------------------------------------------------------

    distance_flags = distance_results[
        distance_results["distance_error"]
    ]

    for _, row in distance_flags.iterrows():

        mask = (
            results["invoice_id"]
            == row["invoice_id"]
        )

        results.loc[
            mask,
            "audit_status"
        ] = "FAIL"

        results.loc[
            mask,
            "error_type"
        ] = "distance_error"

        excess_miles = max(
            row["distance_difference"],
            0
        )

        distance_overcharge = (
            excess_miles
            * (
                row["base_rate_per_mile"]
                + row["fuel_surcharge_rate"]
            )
        )

        results.loc[
            mask,
            "overcharge_amount"
        ] = round(
            distance_overcharge,
            2
        )

        results.loc[
            mask,
            "expected_amount"
        ] = round(
            row["billed_amount"]
            - distance_overcharge,
            2
        )

        results.loc[
            mask,
            "evidence_source"
        ] = "shipment_evidence.csv"

        results.loc[
            mask,
            "actual_value"
        ] = round(
            row["actual_distance_miles_invoice"],
            2
        )

        results.loc[
            mask,
            "expected_value"
        ] = round(
            row["actual_distance_miles_shipment"],
            2
        )

        results.loc[
            mask,
            "explanation"
        ] = (
            "Invoice distance differs from "
            "operational shipment distance."
        )

    # ---------------------------------------------------------
    # RATE
    # ---------------------------------------------------------

    rate_flags = rate_results[
        rate_results["rate_error"]
    ]

    for _, row in rate_flags.iterrows():

        mask = (
            results["invoice_id"]
            == row["invoice_id"]
        )

        results.loc[
            mask,
            "audit_status"
        ] = "FAIL"

        results.loc[
            mask,
            "error_type"
        ] = "rate_error"

        results.loc[
            mask,
            "overcharge_amount"
        ] = round(
            abs(row["base_charge_difference"]),
            2
        )

        results.loc[
            mask,
            "expected_amount"
        ] = round(
            row["billed_amount"]
            - abs(row["base_charge_difference"]),
            2
        )

        results.loc[
            mask,
            "evidence_source"
        ] = "contract_rates.csv"

        results.loc[
            mask,
            "actual_value"
        ] = round(
            row["calculated_base_charge"],
            2
        )

        results.loc[
            mask,
            "expected_value"
        ] = round(
            row["evidence_base_charge"],
            2
        )

        results.loc[
            mask,
            "explanation"
        ] = (
            "Invoice base charge differs from "
            "the contracted rate applied to "
            "the invoiced distance."
        )

    # ---------------------------------------------------------
    # FUEL SURCHARGE
    # ---------------------------------------------------------

    fuel_flags = fuel_results[
        fuel_results["fuel_surcharge_error"]
    ]

    for _, row in fuel_flags.iterrows():

        mask = (
            results["invoice_id"]
            == row["invoice_id"]
        )

        results.loc[
            mask,
            "audit_status"
        ] = "FAIL"

        results.loc[
            mask,
            "error_type"
        ] = "fuel_surcharge_error"

        results.loc[
            mask,
            "overcharge_amount"
        ] = round(
            abs(row["fuel_charge_difference"]),
            2
        )

        results.loc[
            mask,
            "expected_amount"
        ] = round(
            row["billed_amount"]
            - abs(row["fuel_charge_difference"]),
            2
        )

        results.loc[
            mask,
            "evidence_source"
        ] = "contract_rates.csv"

        results.loc[
            mask,
            "actual_value"
        ] = round(
            row["calculated_fuel_surcharge"],
            2
        )

        results.loc[
            mask,
            "expected_value"
        ] = round(
            row["evidence_fuel_charge"],
            2
        )

        results.loc[
            mask,
            "explanation"
        ] = (
            "Invoice fuel surcharge differs "
            "from the contracted surcharge "
            "applied to the invoiced distance."
        )

    # ---------------------------------------------------------
    # DETENTION
    # ---------------------------------------------------------

    detention_flags = detention_results[
        detention_results["detention_error"]
    ]

    for _, row in detention_flags.iterrows():

        mask = (
            results["invoice_id"]
            == row["invoice_id"]
        )

        results.loc[
            mask,
            "audit_status"
        ] = "FAIL"

        results.loc[
            mask,
            "error_type"
        ] = "detention_error"

        results.loc[
            mask,
            "overcharge_amount"
        ] = round(
            abs(
                row["detention_charge_difference"]
            ),
            2
        )

        results.loc[
            mask,
            "expected_amount"
        ] = round(
            row["billed_amount"]
            - abs(
                row["detention_charge_difference"]
            ),
            2
        )

        results.loc[
            mask,
            "evidence_source"
        ] = "delivery_evidence.csv"

        results.loc[
            mask,
            "actual_value"
        ] = round(
            row["calculated_detention_charge"],
            2
        )

        results.loc[
            mask,
            "expected_value"
        ] = round(
            row["evidence_detention_charge"],
            2
        )

        results.loc[
            mask,
            "explanation"
        ] = (
            "Invoice detention charge differs "
            "from detention supported by "
            "delivery-event evidence."
        )

    # ---------------------------------------------------------
    # ACCESSORIAL
    # ---------------------------------------------------------

    accessorial_flags = accessorial_results[
        accessorial_results["accessorial_error"]
    ]

    for _, row in accessorial_flags.iterrows():

        mask = (
            results["invoice_id"]
            == row["invoice_id"]
        )

        results.loc[
            mask,
            "audit_status"
        ] = "FAIL"

        results.loc[
            mask,
            "error_type"
        ] = "accessorial_error"

        results.loc[
            mask,
            "overcharge_amount"
        ] = round(
            abs(row["accessorial_difference"]),
            2
        )

        results.loc[
            mask,
            "expected_amount"
        ] = round(
            row["billed_amount"]
            - abs(row["accessorial_difference"]),
            2
        )

        results.loc[
            mask,
            "evidence_source"
        ] = "load_evidence.csv"

        results.loc[
            mask,
            "actual_value"
        ] = round(
            row["calculated_accessorial_charges"],
            2
        )

        results.loc[
            mask,
            "expected_value"
        ] = round(
            row["accessorial_charges"],
            2
        )

        results.loc[
            mask,
            "explanation"
        ] = (
            "Invoice accessorial charge differs "
            "from the load-level accessorial "
            "evidence."
        )

    return results

def assign_severity(results):

    print("\nAssigning audit severity...")

    results["severity"] = "LOW"

    results.loc[
        results["overcharge_amount"] >= 100,
        "severity"
    ] = "MEDIUM"

    results.loc[
        results["overcharge_amount"] >= 500,
        "severity"
    ] = "HIGH"

    results.loc[
        results["overcharge_amount"] >= 1000,
        "severity"
    ] = "CRITICAL"

    # PASS invoices should not have a severity.
    results.loc[
        results["audit_status"] == "PASS",
        "severity"
    ] = ""

    print("\nSeverity distribution:")

    print(
        results[
            results["audit_status"] == "FAIL"
        ]["severity"]
        .value_counts()
    )

    return results

if __name__ == "__main__":

    (
        invoices,
        contracts,
        shipments,
        deliveries,
        loads,
    ) = load_data()

    distance_results = audit_distance(
        invoices,
        shipments,
    )

    rate_results = audit_rate(
        invoices,
        shipments,
        contracts,
    )

    fuel_results = audit_fuel_surcharge(
        invoices,
        contracts,
    )

    detention_results = audit_detention(
        invoices,
        shipments,
        deliveries,
    )

    accessorial_results = audit_accessorial(
        invoices,
        loads,
    )

    results = build_audit_results(
        invoices,
        distance_results,
        rate_results,
        fuel_results,
        detention_results,
        accessorial_results,
    )

    results = assign_severity(
        results
    )

    output_path = (
        "data/audit_results.csv"
    )

    results.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nAudit results saved to: "
        f"{output_path}"
    )

    print(
        f"Total invoices audited: "
        f"{len(results):,}"
    )

    print(
        f"Failed invoices: "
        f"{(results['audit_status'] == 'FAIL').sum():,}"
    )

    print(
        f"Passed invoices: "
        f"{(results['audit_status'] == 'PASS').sum():,}"
    )