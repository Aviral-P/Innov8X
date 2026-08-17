from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.audit import AuditResponse
from app.services.audit_service import audit_invoice


router = APIRouter(
    prefix="/audits",
    tags=["Audits"],
)


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


@router.post(
    "",
    response_model=AuditResponse,
)
async def create_audit(
    invoice: UploadFile = File(...),
):
    """
    Upload a freight invoice and run the
    Innov8X multimodal audit pipeline.

    Supported:
    - PDF
    - scanned PDF
    - PNG
    - JPG / JPEG
    - WEBP
    - TIFF
    - EML email files
    """

    if not invoice.filename:

        raise HTTPException(
            status_code=400,
            detail="Invoice file is required.",
        )

    extension = Path(
        invoice.filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported document type. "
                "Please upload a PDF, image, TIFF, "
                "or EML freight invoice."
            ),
        )

    try:

        result = await audit_invoice(
            invoice
        )

        return result

    except ValueError as exc:

        message = str(exc)

        if message.startswith(
            "INVALID_INVOICE:"
        ):

            reason = message[
                len("INVALID_INVOICE:")
            ].strip()

            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_invoice",
                    "message": (
                        "Kindly upload a valid freight invoice."
                    ),
                    "reason": reason,
                },
            ) from exc

        raise HTTPException(
            status_code=500,
            detail=f"Invoice audit failed: {message}",
        ) from exc

    except Exception as exc:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Invoice audit failed: {exc}",
        ) from exc