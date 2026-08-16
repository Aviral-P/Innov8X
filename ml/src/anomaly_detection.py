from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from .feature_engineering import MODEL_FEATURES


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "isolation_forest.pkl"
)

SCORES_PATH = (
    PROJECT_ROOT
    / "ml"
    / "outputs"
    / "anomaly_scores.csv"
)


class InvoiceAnomalyDetector:

    def __init__(
        self,
        model_path=MODEL_PATH,
        scores_path=SCORES_PATH
    ):

        self.model = joblib.load(model_path)

        self.reference_scores = None

        # Existing historical anomaly scores can be used
        # to calculate percentile rankings.
        if scores_path.exists():

            scores_df = pd.read_csv(scores_path)

            if "anomaly_score" in scores_df.columns:

                self.reference_scores = (
                    scores_df["anomaly_score"]
                    .dropna()
                    .values
                )

    def calculate_percentile(self, score):

        if self.reference_scores is None:
            return None

        percentile = (
            np.sum(
                self.reference_scores <= score
            )
            / len(self.reference_scores)
            * 100
        )

        return round(float(percentile), 2)

    def risk_level(self, percentile):

        if percentile is None:
            return "UNKNOWN"

        if percentile >= 98:
            return "HIGH"

        if percentile >= 90:
            return "MEDIUM"

        return "LOW"

    def predict(self, feature_df):

        missing = [
            col
            for col in MODEL_FEATURES
            if col not in feature_df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing features: {missing}"
            )

        X = feature_df[
            MODEL_FEATURES
        ].copy()

        # Same cleaning used during feature creation.
        X = X.replace(
            [np.inf, -np.inf],
            np.nan
        )

        X = X.fillna(
            X.median()
        )

        X = X.fillna(0)

        # Isolation Forest prediction.
        predictions = self.model.predict(X)

        # Raw decision function.
        raw_scores = self.model.decision_function(X)

        # Convert so that HIGHER = MORE anomalous.
        anomaly_scores = -raw_scores

        results = pd.DataFrame({
            "invoice_id": feature_df["invoice_id"],
            "anomaly_score": anomaly_scores,
            "is_anomaly": predictions == -1
        })

        results["rank_percentile"] = (
            results["anomaly_score"]
            .apply(self.calculate_percentile)
        )

        results["ml_risk"] = (
            results["rank_percentile"]
            .apply(self.risk_level)
        )

        return results