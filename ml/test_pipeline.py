from pathlib import Path

from src.feature_engineering import load_model_features
from src.anomaly_detection import InvoiceAnomalyDetector


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "outputs"
    / "anomaly_scores.csv"
)


print("Loading finalized model features...")

features = load_model_features()

print("Feature shape:", features.shape)


print("\nRunning Isolation Forest...")

detector = InvoiceAnomalyDetector()

predictions = detector.predict(features)


print("\nPrediction results:")
print(predictions.head(10))


print("\nAnomalies:")
print(
    predictions["is_anomaly"].value_counts()
)


print("\nRisk distribution:")
print(
    predictions["ml_risk"].value_counts()
)


# Save final ML predictions
predictions.to_csv(
    OUTPUT_PATH,
    index=False
)

print(
    f"\nAnomaly scores saved to:\n{OUTPUT_PATH}"
)