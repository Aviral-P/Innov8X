from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "test_invoices"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "INV00000035.pdf"


def money(value):
    return f"${value:,.2f}"


def build_invoice():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=14,
    )

    right = ParagraphStyle(
        "Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "NORTHSTAR FREIGHT LOGISTICS",
            title,
        )
    )

    story.append(
        Paragraph(
            "1234 Logistics Drive<br/>"
            "Dallas, TX 75201<br/>"
            "Phone: (800) 555-0147<br/>"
            "billing@northstarfreight.example",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 18))

    invoice_info = [
        [
            Paragraph("<b>FREIGHT INVOICE</b>", styles["Normal"]),
            "",
        ],
        [
            "Invoice Number",
            "INV00000035",
        ],
        [
            "Invoice Date",
            "2022-01-02",
        ],
        [
            "Shipment Reference",
            "SHP00000035",
        ],
        [
            "Load Reference",
            "LOAD00000035",
        ],
        [
            "Customer",
            "CUST00016",
        ],
    ]

    table = Table(
        invoice_info,
        colWidths=[2.2 * inch, 4.0 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 18))

    # --------------------------------------------------------
    # BILL TO / SHIPMENT
    # --------------------------------------------------------

    addresses = [
        [
            Paragraph("<b>BILL TO</b>", styles["Normal"]),
            Paragraph("<b>SHIPMENT</b>", styles["Normal"]),
        ],
        [
            Paragraph(
                "Customer: CUST00016<br/>" "Freight Account: Enterprise Logistics",
                styles["Normal"],
            ),
            Paragraph(
                "Load Type: Refrigerated<br/>"
                "Origin: Miami, FL<br/>"
                "Destination: Denver, CO",
                styles["Normal"],
            ),
        ],
    ]

    address_table = Table(
        addresses,
        colWidths=[3.1 * inch, 3.1 * inch],
    )

    address_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(address_table)
    story.append(Spacer(1, 18))

    # --------------------------------------------------------
    # SHIPMENT DETAILS
    # --------------------------------------------------------

    shipment_details = [
        ["Shipment Detail", "Value"],
        ["Route", "Miami, FL → Denver, CO"],
        ["Weight", "32,941 lbs"],
        ["Pieces", "8"],
        ["Service Type", "Refrigerated"],
        ["Shipment Date", "2022-01-01"],
    ]

    shipment_table = Table(
        shipment_details,
        colWidths=[2.2 * inch, 4.0 * inch],
    )

    shipment_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(shipment_table)
    story.append(Spacer(1, 18))

    # --------------------------------------------------------
    # CHARGES
    #
    # IMPORTANT:
    # We intentionally do NOT put the contracted
    # rate-per-mile calculation on the invoice.
    # --------------------------------------------------------

    charges = [
        ["Charge Description", "Amount"],
        ["Transportation / Linehaul", money(3886.17)],
        ["Fuel Surcharge", money(575.12)],
        ["Accessorial Charges", money(75.00)],
        ["Detention", money(0.00)],
        ["", ""],
        ["TOTAL AMOUNT DUE", money(4536.29)],
    ]

    charges_table = Table(
        charges,
        colWidths=[4.5 * inch, 1.7 * inch],
        hAlign="RIGHT",
    )

    charges_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 12),
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(charges_table)
    story.append(Spacer(1, 20))

    # --------------------------------------------------------
    # TERMS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "<b>Payment Terms</b>",
            styles["Heading3"],
        )
    )

    story.append(
        Paragraph(
            "Payment due within 30 days of invoice date.<br/>"
            "Please reference invoice number when remitting payment.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "Thank you for your business.",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build_invoice()
    print(f"Created: {OUTPUT_PATH}")
