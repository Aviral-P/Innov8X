import csv
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


AUDIT_RESULTS = (
    PROJECT_ROOT
    / "data"
    / "audit_results.csv"
)

ERROR_BREAKDOWN = (
    PROJECT_ROOT
    / "data"
    / "audit_error_breakdown.csv"
)

SEVERITY_BREAKDOWN = (
    PROJECT_ROOT
    / "data"
    / "audit_severity_breakdown.csv"
)


# ============================================================
# CSV HELPERS
# ============================================================

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


# ============================================================
# DASHBOARD
# ============================================================

def get_dashboard() -> dict:
    audits = read_csv(
        AUDIT_RESULTS
    )

    errors = read_csv(
        ERROR_BREAKDOWN
    )

    severity = read_csv(
        SEVERITY_BREAKDOWN
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_invoices = len(audits)

    failed_invoices = sum(
        1
        for row in audits
        if str(
            row.get("audit_status", "")
        ).upper()
        == "FAIL"
    )

    passed_invoices = (
        total_invoices
        - failed_invoices
    )

    total_overcharge = sum(
        to_float(
            row.get(
                "overcharge_amount"
            )
        )
        for row in audits
    )

    average_overcharge = (
        total_overcharge
        / failed_invoices
        if failed_invoices
        else 0.0
    )

    # --------------------------------------------------------
    # ERROR BREAKDOWN
    #
    # CSV:
    # error_type,invoice_count,overcharge_exposure
    # --------------------------------------------------------

    error_items = []

    for row in errors:
        error_items.append(
            {
                "name": (
                    row.get(
                        "error_type"
                    )
                    or "Unknown"
                ),

                "count": to_int(
                    row.get(
                        "invoice_count"
                    )
                ),

                "amount": to_float(
                    row.get(
                        "overcharge_exposure"
                    )
                ),
            }
        )

    # --------------------------------------------------------
    # SEVERITY BREAKDOWN
    #
    # CSV:
    # severity,invoice_count,overcharge_exposure
    # --------------------------------------------------------

    severity_items = []

    for row in severity:
        severity_items.append(
            {
                "name": (
                    row.get(
                        "severity"
                    )
                    or "Unknown"
                ),

                "count": to_int(
                    row.get(
                        "invoice_count"
                    )
                ),

                "amount": to_float(
                    row.get(
                        "overcharge_exposure"
                    )
                ),
            }
        )

    # --------------------------------------------------------
    # RECENT AUDITS
    # --------------------------------------------------------

    recent_audits = []

    for row in audits[-10:][::-1]:
        recent_audits.append(
            {
                "invoice_id": row.get(
                    "invoice_id",
                    "",
                ),

                "shipment_id": row.get(
                    "shipment_id",
                    "",
                ),

                "load_id": row.get(
                    "load_id",
                    "",
                ),

                "status": row.get(
                    "audit_status",
                    "",
                ),

                "severity": row.get(
                    "severity",
                    "",
                ),

                "overcharge_amount": to_float(
                    row.get(
                        "overcharge_amount"
                    )
                ),
            }
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "summary": {
            "total_invoices": total_invoices,
            "failed_invoices": failed_invoices,
            "passed_invoices": passed_invoices,
            "total_overcharge": total_overcharge,
            "average_overcharge": average_overcharge,
        },

        "breakdown": {
            "errors": error_items,
            "severity": severity_items,
        },

        "recent_audits": recent_audits,
    }