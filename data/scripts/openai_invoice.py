import base64
import json
import mimetypes
import os
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path

import pymupdf
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVOICE_PATH = (
    PROJECT_ROOT
    / "data"
    / "test_invoices"
    / "INV00000035.pdf"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "openai_ocr_output.json"
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".eml",
}


# ============================================================
# DOCUMENT CLASSIFICATION
# ============================================================

def is_supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def classify_document(path: Path) -> dict:
    """
    Determine whether the uploaded document appears
    to be a freight invoice.

    This is intentionally performed before the audit
    pipeline so unrelated documents such as question
    papers are rejected safely.
    """

    pages = build_multimodal_content(path)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": """
You are a document classification system for a freight
invoice auditing platform.

Determine whether the supplied document is a genuine
freight invoice, freight bill, carrier invoice,
transportation invoice, carrier settlement, or equivalent
freight billing document.

Accept documents even if:

- they are scanned
- they are photographed
- they are handwritten
- the layout is unfamiliar
- terminology differs from a standard invoice
- some fields are missing
- the document is multi-page

Reject documents such as:

- school or university question papers
- resumes
- contracts without billing information
- identity documents
- unrelated receipts
- bank statements
- essays
- ordinary letters
- random images

Look for semantic evidence such as:

- freight
- transportation
- carrier
- shipment
- load
- BOL / bill of lading
- PRO
- PO
- linehaul
- fuel surcharge
- accessorial
- detention
- mileage
- freight charges
- amount due
- invoice total
- billing information

Do NOT require any specific field.

Return JSON only:

{
  "is_freight_invoice": true,
  "document_type": "freight_invoice",
  "confidence": 0.95,
  "reason": "Brief explanation"
}
""",
            },
            {
                "role": "user",
                "content": pages,
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "OpenAI returned an empty classification response."
        )

    return parse_json_response(content)


# ============================================================
# PDF RENDERING
# ============================================================

def render_pdf_pages(path: Path) -> list[str]:
    """
    Render every PDF page into a PNG image and return
    base64 encoded images.
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

            images.append(
                base64.b64encode(
                    png_bytes
                ).decode("utf-8")
            )

    finally:
        document.close()

    return images


# ============================================================
# IMAGE
# ============================================================

def encode_image(path: Path) -> str:
    """
    Convert an image file to base64.
    """

    return base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")


# ============================================================
# EMAIL
# ============================================================

def extract_email_content(path: Path) -> list[dict]:
    """
    Extract useful content from an .eml file.

    The email body is included as text and supported
    invoice attachments are converted into multimodal
    content.
    """

    message = BytesParser(
        policy=policy.default
    ).parsebytes(
        path.read_bytes()
    )

    content = []

    body_parts = []

    for part in message.walk():

        if part.is_multipart():
            continue

        content_type = part.get_content_type()

        filename = part.get_filename()

        if filename:

            extension = Path(
                filename
            ).suffix.lower()

            if extension not in SUPPORTED_EXTENSIONS:
                continue

            payload = part.get_payload(
                decode=True
            )

            if not payload:
                continue

            temp_path = (
                PROJECT_ROOT
                / "data"
                / f".email_attachment_{filename}"
            )

            temp_path.write_bytes(payload)

            try:
                content.extend(
                    build_multimodal_content(
                        temp_path
                    )
                )
            finally:
                temp_path.unlink(
                    missing_ok=True
                )

        elif content_type == "text/plain":

            try:
                text = part.get_content()
            except Exception:
                text = ""

            if text:
                body_parts.append(text)

    if body_parts:

        content.insert(
            0,
            {
                "type": "text",
                "text": (
                    "EMAIL BODY:\n\n"
                    + "\n\n".join(body_parts)
                ),
            },
        )

    return content


# ============================================================
# MULTIMODAL INPUT BUILDER
# ============================================================

def build_multimodal_content(
    path: Path,
) -> list[dict]:
    """
    Convert supported document types into a unified
    multimodal representation.

    PDF       -> page images
    Image     -> image
    EML       -> email text + attachments
    """

    path = Path(path)

    extension = path.suffix.lower()

    if extension == ".pdf":

        page_images = render_pdf_pages(path)

        content = [
            {
                "type": "text",
                "text": (
                    f"PDF document: {path.name}\n"
                    f"Pages: {len(page_images)}"
                ),
            }
        ]

        for image in page_images:

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            "data:image/png;base64,"
                            + image
                        ),
                    },
                }
            )

        return content

    if extension in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".tif",
        ".tiff",
    }:

        encoded = encode_image(path)

        mime_type = (
            mimetypes.guess_type(
                path.name
            )[0]
            or "image/jpeg"
        )

        return [
            {
                "type": "text",
                "text": f"Image document: {path.name}",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:{mime_type};base64,"
                        f"{encoded}"
                    ),
                },
            },
        ]

    if extension == ".eml":

        return extract_email_content(path)

    raise ValueError(
        f"Unsupported document type: {extension}"
    )


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(
    content: str,
) -> dict:

    content = content.strip()

    if content.startswith("```"):

        lines = content.splitlines()

        if lines and lines[0].strip().startswith(
            "```"
        ):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(
            lines
        ).strip()

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise RuntimeError(
            "OpenAI response did not contain JSON."
        )

    content = content[
        start : end + 1
    ]

    try:
        return json.loads(content)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            f"Invalid JSON returned by OpenAI: {exc}"
        ) from exc


# ============================================================
# INVOICE EXTRACTION
# ============================================================

def extract_invoice(
    invoice_path=None,
):

    if invoice_path is None:
        invoice_path = INVOICE_PATH

    invoice_path = Path(
        invoice_path
    )

    if not invoice_path.exists():
        raise FileNotFoundError(
            f"Invoice not found: {invoice_path}"
        )

    if not is_supported_file(
        invoice_path
    ):
        raise ValueError(
            "Unsupported document type. "
            "Supported formats: PDF, PNG, JPG, JPEG, "
            "WEBP, TIFF and EML."
        )

    print(
        f"Input document: {invoice_path.name}"
    )

    print(
        "\nClassifying document..."
    )

    classification = classify_document(
        invoice_path
    )

    print(
        "Document type:",
        classification.get(
            "document_type"
        ),
    )

    print(
        "Invoice confidence:",
        classification.get(
            "confidence"
        ),
    )

    if not classification.get(
        "is_freight_invoice",
        False,
    ):

        reason = classification.get(
            "reason",
            "The uploaded document does not appear to be a freight invoice.",
        )

        raise ValueError(
            "INVALID_INVOICE:"
            + reason
        )

    print(
        "\nDocument accepted as freight invoice."
    )

    # --------------------------------------------------------
    # BUILD MULTIMODAL INPUT
    # --------------------------------------------------------

    document_content = (
        build_multimodal_content(
            invoice_path
        )
    )

    # --------------------------------------------------------
    # EXTRACTION
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=2500,
        messages=[
            {
                "role": "system",
                "content": """
You are an expert freight invoice extraction and
normalization system.

Your job is to understand freight invoices regardless
of their visual layout, terminology, document quality,
or source.

The invoice may be:

- digitally generated
- scanned
- photographed
- handwritten
- multi-page
- poorly formatted
- from an unfamiliar carrier
- missing fields
- using terminology different from standard freight
                invoices

Use visual understanding and natural-language understanding.

IMPORTANT RULES:

1. Extract only information actually visible in the document.

2. Never invent values.

3. Never calculate missing values.

4. Missing values must be null.

5. Understand semantic equivalents.

Examples:

Line Haul / Linehaul / Freight / Base Freight /
Transportation Charge
→ transportation_charge

FSC / Fuel / Fuel Surcharge / Fuel Adjustment
→ fuel_charge

Detention / Waiting Time / Waiting Fee
→ detention_charge

Lumper / Toll / Stop Off / Storage / Layover /
Hazmat / Scale Fee
→ additional_charges where appropriate.

6. Preserve the original text of unknown charge descriptions.

7. Do not assume the invoice follows any particular
template.

8. Read every page.

9. Handwritten values should only be returned when
visually readable with reasonable confidence.

10. If a value is unclear, return null instead of guessing.

11. Extract the printed final total. Do not calculate it.

12. Identify the currency if explicitly visible.

13. Do not derive identifiers from other fields.

Return JSON only.
""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract and normalize this freight invoice.

Return exactly this JSON structure:

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
  "currency": null,

  "additional_charges": [],

  "extraction_metadata": {
    "document_type": "freight_invoice",
    "confidence": null,
    "needs_review": false
  }
}

For additional_charges use:

[
  {
    "description": "Original visible description",
    "amount": 0,
    "normalized_type": "accessorial"
  }
]

Possible normalized_type values:

transportation
fuel
accessorial
detention
permit
escort
special_handling
unknown

Set needs_review to true when important financial
information is difficult to read or ambiguous.
""",
                    },
                    *document_content,
                ],
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "OpenAI returned an empty extraction response."
        )

    print(
        "\nRaw OpenAI response:"
    )

    print(
        repr(content)
    )

    result = parse_json_response(
        content
    )

    # Preserve classification information.
    metadata = result.get(
        "extraction_metadata"
    ) or {}

    metadata[
        "document_type"
    ] = "freight_invoice"

    metadata[
        "classifier_confidence"
    ] = classification.get(
        "confidence"
    )

    metadata[
        "classifier_reason"
    ] = classification.get(
        "reason"
    )

    result[
        "extraction_metadata"
    ] = metadata

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    if not INVOICE_PATH.exists():
        raise FileNotFoundError(
            f"Invoice not found: {INVOICE_PATH}"
        )

    print(
        "Running multimodal invoice extraction..."
    )

    print(
        f"Invoice: {INVOICE_PATH}"
    )

    print(
        "Model: gpt-4o-mini"
    )

    invoice = extract_invoice()

    OUTPUT_PATH.write_text(
        json.dumps(
            invoice,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\nExtracted invoice:"
    )

    print(
        json.dumps(
            invoice,
            indent=2,
        )
    )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()