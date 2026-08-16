from fastapi import APIRouter

from app.schemas.ml import (
    MLAnomalyRequest,
    MLAnomalyResponse
)

from app.services.ml_service import predict_anomaly


router = APIRouter(
    prefix="/api/v1/ml",
    tags=["ML Anomaly Detection"]
)


@router.post(
    "/anomaly",
    response_model=MLAnomalyResponse
)
def detect_anomaly(request: MLAnomalyRequest):

    result = predict_anomaly(request.invoice_id)

    return result