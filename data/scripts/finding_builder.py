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
# HELPERS
# ============================================================

def safe_number(value, default=0.0):
    """
    Safely convert numeric values.

    Missing values are represented as the supplied default
    instead of causing the finding builder to crash.
    """
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_text(value, default=""):
    if value is None:
        return default

    return str(value)


# ============================================================
# FINDING BUILDER
# ============================================================

def build_finding(audit):
    """
    Build a human-readable, evidence-backed finding.

    The builder must never invent an audit finding when
    the deterministic auditor could not establish one.
    """

    audit = audit or {}

    checks = audit.get("checks") or {}
    rate = checks.get("rate") or {}

    audit_status = audit.get(
        "audit_status",
        "REVIEW",
    )

    error_types = audit.get(
        "error_types"
    ) or []

    # --------------------------------------------------------
    # IDENTIFIERS
    # --------------------------------------------------------

    invoice_id = audit.get(
        "invoice_id"
    )

    shipment_id = audit.get(
        "shipment_id"
    )

    load_id = audit.get(
        "load_id"
    )

    contract_id = audit.get(
        "contract_id"
    )

    # --------------------------------------------------------
    # COMMON OUTPUT
    # --------------------------------------------------------

    finding = {
        "invoice_id": invoice_id,
        "shipment_id": shipment_id,
        "load_id": load_id,
        "contract_id": contract_id,

        "audit_status": audit_status,

        "severity": audit.get(
            "severity",
            "LOW",
        ),

        "error_types": error_types,

        "overcharge_amount": safe_number(
            audit.get(
                "overcharge_amount"
            )
        ),

        "finding": None,

        "other_checks": {
            "fuel_surcharge": checks.get(
                "fuel_surcharge",
                {
                    "status": "NOT_EVALUATED"
                },
            ),

            "accessorial": checks.get(
                "accessorial",
                {
                    "status": "NOT_EVALUATED"
                },
            ),

            "detention": checks.get(
                "detention",
                {
                    "status": "NOT_EVALUATED"
                },
            ),
        },

        "evidence": audit.get(
            "evidence"
        ) or {},
    }

    # --------------------------------------------------------
    # NO CONFIRMED FINDING
    # --------------------------------------------------------

    if audit_status != "FAIL":
        if audit_status == "PASS":
            finding["finding"] = {
                "type": "none",
                "title": "No billing discrepancy identified",
                "billed_amount": safe_number(
                    audit.get("billed_total")
                ),
                "expected_amount": safe_number(
                    audit.get("expected_total")
                ),
                "variance": safe_number(
                    audit.get("total_variance")
                ),
                "actual_distance_miles": None,
                "contract_rate_per_mile": None,
                "calculation": None,
                "explanation": (
                    "The available operational and contractual "
                    "evidence did not identify a billing discrepancy."
                ),
            }

        else:
            finding["finding"] = {
                "type": "review_required",
                "title": "Invoice requires manual review",
                "billed_amount": safe_number(
                    audit.get("billed_total")
                ),
                "expected_amount": safe_number(
                    audit.get("expected_total")
                ),
                "variance": safe_number(
                    audit.get("total_variance")
                ),
                "actual_distance_miles": None,
                "contract_rate_per_mile": None,
                "calculation": None,
                "explanation": (
                    "The available evidence was insufficient "
                    "to establish a reliable audit finding. "
                    "Manual review is required."
                ),
            }

        return finding

    # --------------------------------------------------------
    # RATE ERROR
    # --------------------------------------------------------

    if "rate_error" in error_types:
        billed_transportation = safe_number(
            rate.get(
                "billed_transportation"
            )
        )

        expected_transportation = safe_number(
            rate.get(
                "expected_transportation"
            )
        )

        variance = safe_number(
            rate.get(
                "variance"
            )
        )

        actual_distance = rate.get(
            "actual_distance"
        )

        contract_rate = rate.get(
            "contract_rate_per_mile"
        )

        if actual_distance is not None:
            distance_text = (
                f"{safe_number(actual_distance):.0f} miles"
            )
        else:
            distance_text = "the operationally supported distance"

        if contract_rate is not None:
            rate_text = (
                f"${safe_number(contract_rate):.2f}/mile"
            )
        else:
            rate_text = "the contracted rate"

        if (
            actual_distance is not None
            and contract_rate is not None
        ):
            calculation = (
                f"{safe_number(actual_distance):.0f} miles "
                f"× ${safe_number(contract_rate):.2f}/mile "
                f"= ${expected_transportation:.2f}"
            )
        else:
            calculation = (
                f"Evidence-supported transportation charge "
                f"= ${expected_transportation:.2f}"
            )

        finding["finding"] = {
            "type": "rate_error",

            "title": (
                "Invoice transportation charge "
                "exceeds contracted rate"
            ),

            "billed_amount": billed_transportation,

            "expected_amount": expected_transportation,

            "variance": variance,

            "actual_distance_miles": (
                safe_number(actual_distance)
                if actual_distance is not None
                else None
            ),

            "contract_rate_per_mile": (
                safe_number(contract_rate)
                if contract_rate is not None
                else None
            ),

            "calculation": calculation,

            "explanation": (
                f"Invoice {safe_text(invoice_id, 'unknown')} "
                f"billed ${billed_transportation:.2f} "
                f"for transportation. "
                f"Contract {safe_text(contract_id, 'unknown')} "
                f"specifies {rate_text}. "
                f"Operational shipment "
                f"{safe_text(shipment_id, 'unknown')} "
                f"supports {distance_text}. "
                f"The evidence-supported transportation "
                f"charge is ${expected_transportation:.2f}, "
                f"creating a variance of ${variance:.2f}."
            ),
        }

        return finding

    # --------------------------------------------------------
    # OTHER CONFIRMED ERROR
    # --------------------------------------------------------

    finding["finding"] = {
        "type": (
            error_types[0]
            if error_types
            else "billing_error"
        ),

        "title": "Invoice billing discrepancy identified",

        "billed_amount": safe_number(
            audit.get("billed_total")
        ),

        "expected_amount": safe_number(
            audit.get("expected_total")
        ),

        "variance": safe_number(
            audit.get("total_variance")
        ),

        "actual_distance_miles": None,

        "contract_rate_per_mile": None,

        "calculation": None,

        "explanation": (
            "A billing discrepancy was identified by the "
            "deterministic evidence audit. See the individual "
            "audit checks and evidence sources for the supporting details."
        ),
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