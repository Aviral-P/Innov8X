import base64
import json
import mimetypes
import os
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
    Determine whether a document is a freight invoice.

    Classification is semantic rather than template based.
    """

    content = build_multimodal_content(path)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": """
You are the document classification layer of
Innov8X, an evidence-driven freight audit platform.

Determine whether the supplied document is a genuine
freight billing document.

ACCEPT:

- freight invoices
- carrier invoices
- freight bills
- transportation invoices
- motor carrier invoices
- carrier settlements containing freight charges
- logistics billing statements
- scanned freight invoices
- photographed freight invoices
- handwritten freight invoices
- multi-page freight invoices
- invoices with unusual layouts
- invoices with missing fields
- invoices containing only some freight fields

The document does NOT need to contain:
- an invoice number
- a shipment number
- a load number
- a BOL
- a PO
- mileage
- a specific charge name
- a specific layout

Use semantic evidence.

Typical freight evidence includes:

- carrier
- transportation
- freight
- shipment
- load
- bill of lading
- BOL
- PRO
- PO
- linehaul
- line haul
- fuel surcharge
- accessorial
- detention
- lumper
- mileage
- delivery
- pickup
- origin
- destination
- freight charges
- amount due
- balance due
- invoice total

REJECT clearly unrelated documents such as:

- school/university question papers
- resumes
- essays
- identity documents
- bank statements
- medical records
- ordinary receipts
- menus
- advertisements
- unrelated contracts
- random photographs
- unrelated letters

IMPORTANT:

Do not reject a freight invoice merely because it is:
- handwritten
- blurry
- scanned
- partially unreadable
- missing fields
- from an unfamiliar carrier
- visually different from other invoices

If it is probably a freight invoice but some information is
unclear, accept it and lower the confidence.

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
                "content": content,
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
    Render every PDF page to PNG and return base64 images.

    This allows both digitally generated PDFs and scanned PDFs
    to be processed through the same vision pipeline.
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
    Extract email body and supported invoice attachments.
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

            temp_directory = (
                PROJECT_ROOT
                / "data"
                / ".email_attachments"
            )

            temp_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            temp_path = (
                temp_directory
                / Path(filename).name
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
                body_parts.append(
                    text
                )

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
    Convert supported documents into multimodal content.

    PDF
        -> every page rendered as PNG

    Image
        -> image input

    EML
        -> email body + supported attachments
    """

    path = Path(path)

    extension = path.suffix.lower()

    if extension == ".pdf":

        page_images = render_pdf_pages(
            path
        )

        content = [
            {
                "type": "text",
                "text": (
                    f"PDF document: {path.name}\n"
                    f"Pages: {len(page_images)}\n"
                    "Read every page before extracting."
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
    }:

        encoded = encode_image(
            path
        )

        mime_type = (
            mimetypes.guess_type(
                path.name
            )[0]
            or "image/jpeg"
        )

        return [
            {
                "type": "text",
                "text": (
                    f"Image document: {path.name}\n"
                    "Inspect all visible text, tables, "
                    "handwriting, labels and totals."
                ),
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

    if extension in {
        ".tif",
        ".tiff",
    }:

        # Convert TIFF to PNG because PNG is a safer
        # multimodal interchange format.

        document = pymupdf.open(
            stream=path.read_bytes(),
            filetype="tiff",
        )

        images = []

        try:

            for page in document:

                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(
                        2,
                        2,
                    ),
                    alpha=False,
                )

                png_bytes = pixmap.tobytes(
                    "png"
                )

                images.append(
                    base64.b64encode(
                        png_bytes
                    ).decode("utf-8")
                )

        finally:

            document.close()

        content = [
            {
                "type": "text",
                "text": (
                    f"TIFF document: {path.name}\n"
                    f"Pages: {len(images)}"
                ),
            }
        ]

        for image in images:

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

    if extension == ".eml":

        return extract_email_content(
            path
        )

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

        return json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Invalid JSON returned by OpenAI: "
            f"{exc}"
        ) from exc


# ============================================================
# INVOICE EXTRACTION
# ============================================================

def extract_invoice(
    invoice_path=None,
):

    if invoice_path is None:

        invoice_path = (
            INVOICE_PATH
        )

    invoice_path = Path(
        invoice_path
    )

    if not invoice_path.exists():

        raise FileNotFoundError(
            f"Invoice not found: "
            f"{invoice_path}"
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
        f"Input document: "
        f"{invoice_path.name}"
    )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

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
            "The uploaded document does not appear "
            "to be a freight invoice.",
        )

        raise ValueError(
            "INVALID_INVOICE:"
            + reason
        )

    print(
        "\nDocument accepted as freight invoice."
    )

    # --------------------------------------------------------
    # MULTIMODAL CONTENT
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
        max_tokens=5000,
        messages=[
            {
                "role": "system",
                "content": """
You are the core multimodal invoice-understanding engine for Innov8X,
an evidence-driven freight audit platform.

Your job is to extract REAL invoice documents into the existing
canonical schema while preserving exactly what the document supports.

You must understand arbitrary freight invoices, not one template or
our synthetic dataset. The document may be a digital PDF, scanned PDF,
image, photograph, handwritten invoice, multi-page invoice, unfamiliar
carrier format, freight bill, carrier statement, or invoice containing
unusual tables and custom charges.

Use BOTH visual understanding and semantic understanding.

============================================================
ABSOLUTE RULES
============================================================

1. Extract ONLY information visibly supported by the document.
2. NEVER invent, guess, repair, or derive an identifier.
3. NEVER treat different identifiers as interchangeable.
4. NEVER calculate a missing invoice value.
5. NEVER replace a printed financial value with a calculated value.
6. If a value is unreadable or ambiguous, return null.
7. Read EVERY page, including headers, footers, tables and totals.
8. Preserve unfamiliar terminology instead of silently discarding it.
9. Do not require every canonical field to exist.
10. Do not assume a carrier, country, template, or dataset layout.
11. If multiple interpretations are possible, return null and set
   needs_review=true.

============================================================
PARTY / ADDRESS SEMANTICS
============================================================

This is critical.

"Bill To", "Billed To", "Customer", "Sold To", "Account"
means the BILLING/CUSTOMER party.

"Ship To", "Deliver To", "Destination", "Delivery Location"
means the SHIPMENT DESTINATION.

"Ship From", "Origin", "Pickup", "Pick-up Location"
means the SHIPMENT ORIGIN.

NEVER map "Bill To" to destination_address simply because it is the
only visible company/address.

If a company/address appears under Bill To, preserve it as meaningful
customer information in raw_fields when no canonical customer field
can represent it.

If a company/address appears under Ship To or Destination, it may
populate destination_address.

If the role of an address is unclear, do not invent the role.

============================================================
DATES
============================================================

Distinguish invoice date, shipment date, pickup date, delivery date
and due date.

Do not put a due date into invoice_date.

Normalize a date only when it is unambiguous.

============================================================
FINANCIAL VALUES
============================================================

For every amount, identify its LABEL/ROW and COLUMN before extracting.

Invoices may contain:
- subtotal
- tax
- freight/linehaul
- fuel surcharge
- accessorials
- detention
- discounts
- credits
- adjustments
- other charges
- total
- amount due
- balance due

Do not assume the last number on a page is the total.

Do not move a nearby number into another column.

============================================================
GRAND TOTAL
============================================================

grand_total MUST be the FINAL PRINTED invoice total / Total Due /
Amount Due / Balance Due / Grand Total visibly shown.

NEVER calculate grand_total from subtotal, tax or line items.

If the printed final total is missing or unreadable:
grand_total = null
and needs_review=true.

If printed totals are internally inconsistent, preserve the printed
values exactly. DO NOT "fix" them.

Example:
Subtotal $2450.00
Tax $138.75
Total Due $2450.00

Return subtotal=2450, tax=138.75, grand_total=2450.
Do NOT change grand_total to 2588.75.
Set needs_review=true and explain the inconsistency.

============================================================
LINE ITEM / TABLE READING
============================================================

When a charge table exists, extract EACH actual visible row exactly once.

For each row:
- description = visible description
- quantity = quantity/units column
- unit = visible unit
- unit_price = rate/price column
- amount = row total/extended amount
- category = semantic category

CRITICAL:
Do not assume quantity × unit_price equals amount.

Do not shift values between columns.

If column association is unclear, use null for the uncertain field
instead of guessing.

If the same description appears in multiple actual rows, preserve
each row once.

============================================================
CHARGES
============================================================

Map semantically:

Linehaul / Line Haul / Freight / Base Freight / Transportation
/ Transportation Charge / Transport Charge
-> transportation_charge

FSC / Fuel / Fuel Surcharge / Fuel Adjustment / Diesel Surcharge
-> fuel_charge

Detention / Waiting Time / Waiting Charge / Waiting Fee
-> detention_charge

Lumper / Toll / Scale / Stop Off / Layover / Storage / Hazmat /
Handling
-> additional_charges or accessorial_charge as appropriate

Permit -> permits_charge
Escort -> escorts_charge
Special Handling -> special_handling_charge

Unknown charges MUST be preserved in additional_charges with their
original visible description and normalized_type="unknown".

============================================================
IDENTIFIERS
============================================================

Extract independently:
- invoice number
- shipment reference
- load reference
- BOL
- PRO
- PO
- customer reference
- carrier reference
- trip reference
- account number
- booking number
- order number

Do not convert "Shipment #123" into load_reference.
Do not convert "PO 123" into shipment_reference.
Do not convert "Invoice #123" into shipment_reference.

Only populate a canonical identifier when its label/context supports
that mapping.

============================================================
MILEAGE / LOGISTICS
============================================================

Populate mileage fields ONLY when mileage/odometer values are
explicitly visible.

Do NOT infer road distance from origin/destination.
Do NOT infer GPS distance.
Do NOT calculate mileage from a map.
Do NOT calculate loaded/empty mileage from another field.

============================================================
RAW FIELDS
============================================================

Use raw_fields for meaningful document-specific information that does
not fit the canonical schema.

Useful examples:
- bill_to_name
- bill_to_address
- due_date
- service_level
- freight_class
- weight
- pieces
- commodity
- accessorial_code
- fuel_index
- payment_method
- carrier_account_number

Do not duplicate canonical fields inside raw_fields.

============================================================
CONFIDENCE / REVIEW
============================================================

Set confidence from 0 to 1.

Set needs_review=true when:
- important financial values are unclear
- invoice total is missing
- subtotal/tax/total appear inconsistent
- an important identifier is unreadable
- handwriting is ambiguous
- table columns cannot be reliably interpreted
- multiple interpretations are possible
- the document is incomplete
- extraction quality is poor

A freight invoice may still be accepted when needs_review=true.

============================================================
RETURN JSON ONLY
============================================================

Use the exact existing JSON structure below.
Do not add prose outside JSON.

{
  "invoice_number": null,
  "invoice_date": null,

  "shipment_reference": null,
  "load_reference": null,

  "customer_id": null,

  "po_number": null,
  "bol_number": null,
  "pro_number": null,

  "carrier_name": null,
  "carrier_reference": null,

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

  "subtotal": null,
  "tax": null,
  "grand_total": null,

  "currency": null,

  "payment_terms": null,

  "additional_charges": [],

  "line_items": [],

  "additional_references": [],

  "raw_fields": {},

  "extraction_metadata": {
    "document_type": "freight_invoice",
    "confidence": null,
    "needs_review": false,
    "missing_critical_fields": [],
    "review_reasons": []
  }
}

For additional_charges:
[
  {
    "description": "Original visible description",
    "amount": 0,
    "normalized_type": "accessorial"
  }
]

normalized_type must be:
transportation, fuel, accessorial, detention, permit, escort,
special_handling, unknown.

For line_items:
[
  {
    "description": "Line haul",
    "quantity": 1,
    "unit": "load",
    "unit_price": 2500,
    "amount": 2500,
    "category": "transportation"
  }
]

For additional_references:
[
  {
    "type": "BOL",
    "value": "123456789"
  }
]
""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract the freight invoice "
                            "from the following document. "
                            "Read every page/image carefully."
                        ),
                    },
                    *document_content,
                ],
            },
        ],
    )

    content = (
        response.choices[0].message.content
    )

    if not content:

        raise RuntimeError(
            "OpenAI returned an empty invoice extraction response."
        )

    print(
        "\nRaw OpenAI response:"
    )

    print(
        repr(content)
    )

    extracted = parse_json_response(
        content
    )

    # --------------------------------------------------------
    # SAFETY / METADATA
    # --------------------------------------------------------

    metadata = (
        extracted.get(
            "extraction_metadata"
        )
        or {}
    )

    # --------------------------------------------------------
    # DETERMINISTIC EXTRACTION SANITY CHECKS
    # --------------------------------------------------------
    # Never modify printed invoice values here. These checks only
    # identify suspicious extraction results and request review.

    review_reasons = list(
        metadata.get("review_reasons")
        or []
    )

    subtotal = extracted.get("subtotal")
    tax = extracted.get("tax")
    grand_total = extracted.get("grand_total")

    if (
        isinstance(subtotal, (int, float))
        and isinstance(tax, (int, float))
        and isinstance(grand_total, (int, float))
    ):
        calculated_total = round(
            float(subtotal) + float(tax),
            2,
        )

        if abs(calculated_total - float(grand_total)) > 0.01:
            reason = (
                "printed subtotal, tax and final total "
                "appear internally inconsistent"
            )

            if reason not in review_reasons:
                review_reasons.append(reason)

    line_items = extracted.get("line_items")

    if isinstance(line_items, list):
        for item in line_items:
            if not isinstance(item, dict):
                continue

            if (
                item.get("description")
                and item.get("amount") is None
            ):
                reason = (
                    "one or more visible invoice line items "
                    "have an unreadable amount"
                )

                if reason not in review_reasons:
                    review_reasons.append(reason)

                break

    metadata["review_reasons"] = review_reasons

    metadata[
        "document_type"
    ] = classification.get(
        "document_type",
        "freight_invoice",
    )

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

    # Extraction confidence is different from
    # classification confidence.

    extraction_confidence = (
        metadata.get(
            "confidence"
        )
    )

    if extraction_confidence is None:

        extraction_confidence = (
            classification.get(
                "confidence"
            )
        )

    metadata[
        "confidence"
    ] = extraction_confidence

    # --------------------------------------------------------
    # REVIEW DETECTION
    # --------------------------------------------------------

    review_reasons = list(
        metadata.get(
            "review_reasons"
        )
        or []
    )

    missing_critical_fields = list(
        metadata.get(
            "missing_critical_fields"
        )
        or []
    )

    if extracted.get(
        "grand_total"
    ) is None:

        missing_critical_fields.append(
            "grand_total"
        )

        if (
            "final invoice total is missing or unreadable"
            not in review_reasons
        ):
            review_reasons.append(
                "final invoice total is missing or unreadable"
            )

    if extracted.get(
        "invoice_number"
    ) is None:

        # This is not necessarily fatal for freight
        # invoice processing, but makes matching harder.

        missing_critical_fields.append(
            "invoice_number"
        )

    # De-duplicate while preserving order.

    metadata[
        "missing_critical_fields"
    ] = list(
        dict.fromkeys(
            missing_critical_fields
        )
    )

    metadata[
        "review_reasons"
    ] = list(
        dict.fromkeys(
            review_reasons
        )
    )

    metadata[
        "needs_review"
    ] = bool(
        metadata.get(
            "needs_review",
            False,
        )
        or metadata[
            "review_reasons"
        ]
    )

    extracted[
        "extraction_metadata"
    ] = metadata

    # --------------------------------------------------------
    # BACKWARD COMPATIBILITY
    # --------------------------------------------------------
    #
    # The existing Innov8X audit engine expects these
    # canonical fields. New arbitrary fields are preserved
    # separately rather than breaking the existing pipeline.
    # --------------------------------------------------------

    canonical_defaults = {
        "invoice_number": None,
        "invoice_date": None,
        "shipment_reference": None,
        "load_reference": None,
        "customer_id": None,
        "po_number": None,
        "bol_number": None,
        "operator_name": None,
        "truck_number": None,
        "pickup_address": None,
        "pickup_contact": None,
        "destination_address": None,
        "destination_contact": None,
        "loaded_mileage_start": None,
        "loaded_mileage_end": None,
        "loaded_mileage_total": None,
        "empty_mileage_start": None,
        "empty_mileage_end": None,
        "empty_mileage_total": None,
        "transportation_charge": None,
        "fuel_charge": None,
        "accessorial_charge": None,
        "detention_charge": None,
        "permits_charge": None,
        "escorts_charge": None,
        "special_handling_charge": None,
        "grand_total": None,
        "currency": None,
        "additional_charges": [],
    }

    for field, default in canonical_defaults.items():

        if field not in extracted:

            if isinstance(
                default,
                list,
            ):
                extracted[field] = list(
                    default
                )
            else:
                extracted[field] = default

    # --------------------------------------------------------
    # SAVE DEBUG OUTPUT
    # --------------------------------------------------------

    try:

        OUTPUT_PATH.write_text(
            json.dumps(
                extracted,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            f"\nSaved to: "
            f"{OUTPUT_PATH}"
        )

    except Exception as exc:

        print(
            "Warning: could not save extraction output:",
            exc,
        )

    return extracted


# ============================================================
# CLI
# ============================================================

def main():

    import sys

    if len(sys.argv) > 1:

        path = Path(
            sys.argv[1]
        ).expanduser().resolve()

    else:

        path = INVOICE_PATH

    try:

        result = extract_invoice(
            path
        )

        print(
            "\nExtracted invoice:"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )

    except ValueError as exc:

        message = str(exc)

        if message.startswith(
            "INVALID_INVOICE:"
        ):

            reason = message[
                len("INVALID_INVOICE:")
            :].strip()

            print(
                "\nINVALID INVOICE"
            )

            print(
                "Kindly upload a valid freight invoice."
            )

            print(
                f"Reason: {reason}"
            )

        else:

            print(
                f"\nERROR: {exc}"
            )

        raise

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        raise


if __name__ == "__main__":
    main()