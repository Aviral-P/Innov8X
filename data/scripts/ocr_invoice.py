import json
import subprocess
from pathlib import Path

from normalize_invoice import normalize_invoice


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVOICE_PATH = (
    PROJECT_ROOT
    / "data"
    / "test_invoices"
    / "INV00000035.png"
)
OUTPUT_PATH = PROJECT_ROOT / "data" / "ocr_output.json"


PROMPT = r"""
Analyze this freight invoice and return ONLY valid JSON.

Extract only information explicitly visible in the invoice.
Do not guess, infer, calculate, or invent missing values.
Use null when a field is not visible or cannot be determined.

Return exactly this schema:

{
  "invoice_number": null,
  "invoice_date": null,
  "po_number": null,
  "bol_number": null,
  "operator_name": null,
  "truck_number": null,
  "pickup_address": null,
  "pickup_contact": null,
  "destination_address": null,
  "destination_contact": null,
  "loaded_mileage_start": null,
  "loaded_mileage_end": null,
  "loaded_mileage_total": null,
  "empty_mileage_start": null,
  "empty_mileage_end": null,
  "empty_mileage_total": null,
  "transportation_charge": null,
  "fuel_charge": null,
  "permits_charge": null,
  "escorts_charge": null,
  "special_handling_charge": null,
  "grand_total": null,
  "currency": null
}

Return numbers as numbers.
Do not use commas or currency symbols inside numeric values.
"""


def extract_json(text: str) -> dict:
    """
    Extract the JSON object from the model response.

    Handles responses that accidentally contain
    markdown code fences around the JSON.
    """

    text = text.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1]
        text = text.split("```", 1)[0]

    elif "```" in text:
        text = text.split("```", 1)[1]
        text = text.split("```", 1)[0]

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object found in Ollama response."
        )

    return json.loads(text[start:end + 1])


def run_ocr() -> dict:
    """
    Send the invoice image to Ollama/GLM-OCR.
    """

    if not INVOICE_PATH.exists():
        raise FileNotFoundError(
            f"Invoice not found: {INVOICE_PATH}"
        )

    command = [
        "ollama",
        "run",
        "glm-ocr",
        PROMPT,
        str(INVOICE_PATH),
    ]

    print("Running GLM-OCR...")
    print(f"Invoice: {INVOICE_PATH}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return extract_json(result.stdout)


def main():
    raw_invoice = run_ocr()

    print("\nRaw OCR extraction:")
    print(
        json.dumps(
            raw_invoice,
            indent=2,
        )
    )

    normalized_invoice = normalize_invoice(
        raw_invoice
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            normalized_invoice,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nNormalized invoice:")
    print(
        json.dumps(
            normalized_invoice,
            indent=2,
        )
    )

    print(
        f"\nSaved normalized invoice to:"
        f" {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()