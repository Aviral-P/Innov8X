from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.audit import AuditResponse
from app.services.audit_service import audit_invoice


router = APIRouter(
    prefix="/audits",
    tags=["Audits"],
)


@router.post(
    "",
    response_model=AuditResponse,
)
async def create_audit(
    invoice: UploadFile = File(...),
):
    """
    Upload a freight invoice PDF and run the
    Innov8X audit pipeline.
    """

    if not invoice.filename:
        raise HTTPException(
            status_code=400,
            detail="Invoice file is required.",
        )

    if not invoice.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF invoices are supported.",
        )

    try:
        result = await audit_invoice(invoice)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invoice audit failed: {exc}",
        ) from exc