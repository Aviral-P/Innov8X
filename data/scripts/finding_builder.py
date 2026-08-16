import json
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AUDIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "invoice_audit_result.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "invoice_finding.json"
)


# ============================================================
# FINDING BUILDER
# ============================================================

def build_finding(audit):

    rate = audit["checks"]["rate"]

    finding = {
        "invoice_id": audit["invoice_id"],
        "shipment_id": audit["shipment_id"],
        "load_id": audit["load_id"],
        "contract_id": audit["contract_id"],

        "audit_status": audit["audit_status"],
        "severity": audit["severity"],

        "error_types": audit["error_types"],

        "overcharge_amount": audit[
            "overcharge_amount"
        ],

        "finding": {
            "type": "rate_error",

            "title": (
                "Invoice transportation charge "
                "exceeds contracted rate"
            ),

            "billed_amount": rate[
                "billed_transportation"
            ],

            "expected_amount": rate[
                "expected_transportation"
            ],

            "variance": rate[
                "variance"
            ],

            "actual_distance_miles": rate[
                "actual_distance"
            ],

            "contract_rate_per_mile": rate[
                "contract_rate_per_mile"
            ],

            "calculation": (
                f'{rate["actual_distance"]:.0f} miles '
                f'× ${rate["contract_rate_per_mile"]:.2f}/mile '
                f'= ${rate["expected_transportation"]:.2f}'
            ),

            "explanation": (
                f'Invoice {audit["invoice_id"]} billed '
                f'${rate["billed_transportation"]:.2f} '
                f'for transportation. '
                f'Contract {audit["contract_id"]} '
                f'specifies a rate of '
                f'${rate["contract_rate_per_mile"]:.2f}/mile. '
                f'Operational shipment '
                f'{audit["shipment_id"]} records '
                f'{rate["actual_distance"]:.0f} miles. '
                f'The evidence-supported transportation '
                f'charge is '
                f'${rate["expected_transportation"]:.2f}, '
                f'creating a variance of '
                f'${rate["variance"]:.2f}.'
            ),
        },

        "other_checks": {
            "fuel_surcharge": audit[
                "checks"
            ]["fuel_surcharge"],

            "accessorial": audit[
                "checks"
            ]["accessorial"],

            "detention": audit[
                "checks"
            ]["detention"],
        },

        "evidence": audit["evidence"],
    }

    return finding


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading audit result..."
    )

    with open(
        AUDIT_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        audit = json.load(f)

    print(
        "Building audit finding..."
    )

    finding = build_finding(
        audit
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            finding,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\nAudit finding:"
    )

    print(
        json.dumps(
            finding,
            indent=2,
        )
    )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()