from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ANOMALY_SCORES_PATH = (
    PROJECT_ROOT
    / "ml"
    / "outputs"
    / "anomaly_scores.csv"
)


# ---------------------------------------------------------
# Load precomputed ML results
# ---------------------------------------------------------

anomaly_df = pd.read_csv(ANOMALY_SCORES_PATH)


# ---------------------------------------------------------
# Validate required columns
# ---------------------------------------------------------

REQUIRED_COLUMNS = [
    "invoice_id",
    "anomaly_score",
    "is_anomaly",
    "rank_percentile",
    "ml_risk",
]

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in anomaly_df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns in anomaly_scores.csv: "
        f"{missing_columns}"
    )


# ---------------------------------------------------------
# Prediction function
# ---------------------------------------------------------

def predict_anomaly(invoice_id: str):

    # Find invoice
    result = anomaly_df[
        anomaly_df["invoice_id"] == invoice_id
    ]

    if result.empty:
        raise ValueError(
            f"Invoice '{invoice_id}' not found in anomaly_scores.csv"
        )

    row = result.iloc[0]

    return {
        "invoice_id": str(row["invoice_id"]),
        "anomaly_score": round(
            float(row["anomaly_score"]), 3
        ),
        "is_anomaly": bool(row["is_anomaly"]),
        "ml_risk": str(row["ml_risk"]),
        "rank_percentile": round(
            float(row["rank_percentile"]), 2
        ),
    }