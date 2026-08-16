from pydantic import BaseModel


class MLAnomalyRequest(BaseModel):
    invoice_id: str


class MLAnomalyResponse(BaseModel):
    invoice_id: str
    anomaly_score: float
    is_anomaly: bool
    ml_risk: str
    rank_percentile: float