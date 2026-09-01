"""Point-in-Time Data Access Layer simulating a production database."""

import pandas as pd
from pathlib import Path

class PointInTimeStore:
    _instance = None

    def __init__(self, data_dir: Path | str = "data/synthetic_v2"):
        self.data_dir = Path(data_dir)
        # Load the frozen V2 synthetic datasets into memory
        self.merchants = pd.read_csv(self.data_dir / "merchant_labels.csv")
        self.transactions = pd.read_csv(self.data_dir / "transactions.csv", parse_dates=["timestamp"])
        self.relationships = pd.read_csv(self.data_dir / "relationships.csv", parse_dates=["start_time", "end_time"])

    @classmethod
    def get_instance(cls, data_dir: Path | str = "data/synthetic_v2") -> "PointInTimeStore":
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    def get_merchant(self, merchant_id: str) -> pd.DataFrame:
        """Fetch a specific merchant record."""
        return self.merchants[self.merchants["merchant_id"] == merchant_id].copy()

    def get_merchant_transactions(self, merchant_id: str, end_timestamp: str, lookback_days: int = 90) -> pd.DataFrame:
        """Fetch transactions for a merchant strictly before or at end_timestamp."""
        end_ts = pd.Timestamp(end_timestamp)
        start_ts = end_ts - pd.Timedelta(days=lookback_days)
        
        mask = (
            (self.transactions["merchant_id"] == merchant_id) &
            (self.transactions["timestamp"] <= end_ts) &
            (self.transactions["timestamp"] >= start_ts)
        )
        return self.transactions[mask].copy()

    def get_active_relationships(self, merchant_id: str, end_timestamp: str) -> pd.DataFrame:
        """Fetch relationships for a merchant that were established on or before end_timestamp."""
        end_ts = pd.Timestamp(end_timestamp)
        mask = (
            (self.relationships["merchant_id"] == merchant_id) &
            (self.relationships["start_time"] <= end_ts)
        )
        return self.relationships[mask].copy()

    def get_network_subgraph(self, merchant_id: str, end_timestamp: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Fetch merchants, transactions, and relationships for the 1-hop network around merchant_id.
        This provides the minimal bounded dataset required to perfectly emulate the global 
        graph calculations for a single target merchant.
        """
        end_ts = pd.Timestamp(end_timestamp)
        window_start = end_ts - pd.Timedelta(days=30)
        
        # 1. Local relationships (<= end_ts)
        local_rels = self.get_active_relationships(merchant_id, end_timestamp)
        
        if local_rels.empty:
            return self.get_merchant(merchant_id), self.get_merchant_transactions(merchant_id, end_timestamp), local_rels
            
        # 2. Identify active shared entities within the 30-day window
        active_local_rels = local_rels[local_rels["end_time"] > window_start]
        shared_entities = active_local_rels["entity_id"].unique()
        
        # 3. Find all merchants sharing those entities
        shared_mask = (
            (self.relationships["entity_id"].isin(shared_entities)) & 
            (self.relationships["start_time"] <= end_ts) & 
            (self.relationships["end_time"] > window_start)
        )
        network_rels = self.relationships[shared_mask]
        network_merchants = network_rels["merchant_id"].unique()
        
        # 4. We need all historical relationships for these network merchants up to end_ts
        all_network_rels_mask = (
            (self.relationships["merchant_id"].isin(network_merchants)) & 
            (self.relationships["start_time"] <= end_ts)
        )
        all_network_rels = self.relationships[all_network_rels_mask].copy()
        
        # 5. Fetch transactions for all network merchants within the 90 day lookback
        start_ts = end_ts - pd.Timedelta(days=90)
        tx_mask = (
            (self.transactions["merchant_id"].isin(network_merchants)) & 
            (self.transactions["timestamp"] <= end_ts) & 
            (self.transactions["timestamp"] >= start_ts)
        )
        network_tx = self.transactions[tx_mask].copy()
        
        # 6. Fetch merchants
        network_m = self.merchants[self.merchants["merchant_id"].isin(network_merchants)].copy()
        
        return network_m, network_tx, all_network_rels
