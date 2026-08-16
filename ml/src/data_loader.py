from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_invoices():
    return pd.read_csv(DATA_DIR / "invoices.csv")


def load_shipment_evidence():
    return pd.read_csv(DATA_DIR / "shipment_evidence.csv")


def load_load_evidence():
    return pd.read_csv(DATA_DIR / "load_evidence.csv")


def load_delivery_evidence():
    return pd.read_csv(DATA_DIR / "delivery_evidence.csv")


def load_trip_evidence():
    return pd.read_csv(DATA_DIR / "trip_evidence.csv")


def load_contract_rates():
    return pd.read_csv(DATA_DIR / "contract_rates.csv")


def load_all_data():
    """
    Load all datasets required by the ML pipeline.
    """

    return {
        "invoices": load_invoices(),
        "shipments": load_shipment_evidence(),
        "loads": load_load_evidence(),
        "deliveries": load_delivery_evidence(),
        "trips": load_trip_evidence(),
        "contracts": load_contract_rates(),
    }