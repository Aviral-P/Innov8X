import base64
import json
import os
from pathlib import Path
import pymupdf
from openai import OpenAI
from dotenv import load_dotenv

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVOICE_PATH = PROJECT_ROOT / "data" / "test_invoices" / "INV00000035.pdf"

OUTPUT_PATH = PROJECT_ROOT / "data" / "openai_ocr_output.json"


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)


# ============================================================
# PDF
# ============================================================


def render_pdf_pages(path: Path) -> list[str]:
    """
    Render every PDF page as a PNG and return
    base64-encoded images.
    """

    document = pymupdf.open(path)

    images = []

    try:
        for page in document:

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False,
            )

            png_bytes = pixmap.tobytes("png")

            images.append(base64.b64encode(png_bytes).decode("utf-8"))

    finally:
        document.close()

    return images


# ============================================================
# EXTRACTION
# ============================================================


def extract_invoice():
    page_images = render_pdf_pages(INVOICE_PATH)
    print(
        f"PDF pages rendered: {len(page_images)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": """
You are a freight invoice data extraction system.

Extract ONLY information explicitly visible
in the invoice.

Do not calculate.
Do not infer.
Do not invent missing values.

Extract invoice_number, shipment_reference,
load_reference, and customer_id exactly as
printed on the document.

Do not derive these identifiers from other fields.

Return valid JSON only.

Use null when a field is not present.
Return monetary values as numbers without
currency symbols or commas.
Return mileage as numbers.
""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract this freight invoice using exactly
this JSON schema:

{
  "invoice_number": null,
  "invoice_date": null,
  "shipment_reference": null,
  "load_reference": null,
  "customer_id": null,
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
  "accessorial_charge": null,
  "detention_charge": null,
  "permits_charge": null,
  "escorts_charge": null,
  "special_handling_charge": null,
  "grand_total": null,
  "currency": null
}

Important:

Read ALL pages of the invoice.

Extract information from any page where it appears.

Read the charge table carefully.
Do not omit monetary values that are clearly visible.

For "grand_total", extract the exact final amount
printed on the invoice, such as "TOTAL AMOUNT DUE",
"GRAND TOTAL", or equivalent.

Do NOT calculate grand_total from the individual charges.

If the final total appears on another page,
use that printed value.
""",
                    },
                    *[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": ("data:image/png;base64," f"{page_image}")
                            },
                        }
                        for page_image in page_images
                    ],
                ],
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("OpenAI returned an empty response.")

    print("\nRaw OpenAI response:")
    print(repr(content))

    content = content.strip()

    # Remove markdown JSON fences if the model added them.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    # If the model added text around the JSON,
    # extract the JSON object itself.
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError("OpenAI response did not contain a JSON object.")

    content = content[start : end + 1]

    return json.loads(content)


# ============================================================
# MAIN
# ============================================================


def main():

    if not INVOICE_PATH.exists():
        raise FileNotFoundError(f"Invoice not found: {INVOICE_PATH}")

    print("Running OpenAI invoice extraction...")
    print(f"Invoice: {INVOICE_PATH}")
    print("Input type: PDF")
    print("Model: gpt-4o-mini")

    invoice = extract_invoice()

    OUTPUT_PATH.write_text(
        json.dumps(
            invoice,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nExtracted invoice:")
    print(
        json.dumps(
            invoice,
            indent=2,
        )
    )

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
