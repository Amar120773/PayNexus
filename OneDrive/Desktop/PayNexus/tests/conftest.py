import pytest
import pandas as pd
from pathlib import Path

# Important: We must mock the store before app is imported by any tests
from src.inference.store import PointInTimeStore

class FakeTestStore(PointInTimeStore):
    """
    A test-only mock store that implements PointInTimeStore using pandas.
    This replaces the removed CsvPointInTimeStore so that API tests can run
    without requiring a live Neo4j database, ensuring test isolation.
    """
    def __init__(self, data_dir="data/synthetic_v2"):
        self.data_dir = Path(data_dir)
        self.merchants = pd.read_csv(self.data_dir / "merchant_labels.csv")
        self.transactions = pd.read_csv(self.data_dir / "transactions.csv", parse_dates=["timestamp"])
        self.relationships = pd.read_csv(self.data_dir / "relationships.csv", parse_dates=["start_time", "end_time"])

    def get_merchant(self, merchant_id: str) -> pd.DataFrame:
        return self.merchants[self.merchants["merchant_id"] == merchant_id].copy()

    def get_merchant_transactions(self, merchant_id: str, end_timestamp: str, lookback_days: int = 90) -> pd.DataFrame:
        end_ts = pd.Timestamp(end_timestamp)
        start_ts = end_ts - pd.Timedelta(days=lookback_days)
        mask = (
            (self.transactions["merchant_id"] == merchant_id) &
            (self.transactions["timestamp"] <= end_ts) &
            (self.transactions["timestamp"] >= start_ts)
        )
        return self.transactions[mask].copy()

    def get_active_relationships(self, merchant_id: str, end_timestamp: str) -> pd.DataFrame:
        end_ts = pd.Timestamp(end_timestamp)
        mask = (
            (self.relationships["merchant_id"] == merchant_id) &
            (self.relationships["start_time"] <= end_ts)
        )
        return self.relationships[mask].copy()

    def get_network_subgraph(self, merchant_id: str, end_timestamp: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        end_ts = pd.Timestamp(end_timestamp)
        window_start = end_ts - pd.Timedelta(days=30)
        
        local_rels = self.get_active_relationships(merchant_id, end_timestamp)
        if local_rels.empty:
            return self.get_merchant(merchant_id), self.get_merchant_transactions(merchant_id, end_timestamp), local_rels
            
        active_local_rels = local_rels[local_rels["end_time"] > window_start]
        shared_entities = active_local_rels["entity_id"].unique()
        
        shared_mask = (
            (self.relationships["entity_id"].isin(shared_entities)) & 
            (self.relationships["start_time"] <= end_ts) & 
            (self.relationships["end_time"] > window_start)
        )
        network_rels = self.relationships[shared_mask]
        network_merchants = network_rels["merchant_id"].unique()
        
        all_network_rels_mask = (
            (self.relationships["merchant_id"].isin(network_merchants)) & 
            (self.relationships["start_time"] <= end_ts)
        )
        all_network_rels = self.relationships[all_network_rels_mask].copy()
        
        start_ts = end_ts - pd.Timedelta(days=90)
        tx_mask = (
            (self.transactions["merchant_id"].isin(network_merchants)) & 
            (self.transactions["timestamp"] <= end_ts) & 
            (self.transactions["timestamp"] >= start_ts)
        )
        network_tx = self.transactions[tx_mask].copy()
        network_m = self.merchants[self.merchants["merchant_id"].isin(network_merchants)].copy()
        
        return network_m, network_tx, all_network_rels

# Globally inject the fake store instance so no test hits the production fail-closed logic
PointInTimeStore._instance = FakeTestStore()

@pytest.fixture(autouse=True)
def ensure_fake_store():
    # Make sure tests that intentionally clear _instance (like test_store.py) restore it
    yield
    if not isinstance(PointInTimeStore._instance, FakeTestStore):
        PointInTimeStore._instance = FakeTestStore()
