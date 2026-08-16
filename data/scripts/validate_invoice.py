import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "ocr_output.json"


def validate_invoice(invoice: dict) -> list[str]:
    issues = []

    # --------------------------------------------------------
    # LOADED MILEAGE
    # --------------------------------------------------------

    loaded_start = invoice.get("loaded_mileage_start")
    loaded_end = invoice.get("loaded_mileage_end")
    loaded_total = invoice.get("loaded_mileage_total")

    if (
        loaded_start is not None
        and loaded_end is not None
        and loaded_total is not None
    ):
        calculated = loaded_end - loaded_start

        if abs(calculated - loaded_total) > 1:
            issues.append(
                "Loaded mileage is internally inconsistent."
            )

    # --------------------------------------------------------
    # EMPTY MILEAGE
    # --------------------------------------------------------

    empty_start = invoice.get("empty_mileage_start")
    empty_end = invoice.get("empty_mileage_end")
    empty_total = invoice.get("empty_mileage_total")

    if (
        empty_start is not None
        and empty_end is not None
        and empty_total is not None
    ):
        calculated = empty_end - empty_start

        if abs(calculated - empty_total) > 1:
            issues.append(
                "Empty mileage is internally inconsistent."
            )

    # --------------------------------------------------------
    # TOTAL CHARGES
    # --------------------------------------------------------

    charges = [
        invoice.get("transportation_charge"),
        invoice.get("fuel_charge"),
        invoice.get("permits_charge"),
        invoice.get("escorts_charge"),
        invoice.get("special_handling_charge"),
    ]

    if all(value is not None for value in charges):
        calculated_total = sum(charges)
        grand_total = invoice.get("grand_total")

        if (
            grand_total is not None
            and abs(calculated_total - grand_total) > 0.01
        ):
            issues.append(
                "Grand total does not match extracted charge components."
            )

    return issues


def main():
    invoice = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    issues = validate_invoice(invoice)

    print("\nInvoice validation")
    print("==================")

    if not issues:
        print("No internal inconsistencies detected.")
        return

    print(f"Issues detected: {len(issues)}")

    for issue in issues:
        print(f"- {issue}")


if __name__ == "__main__":
    main()