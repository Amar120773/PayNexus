import pandas as pd
import pytest
from src.inference.store import PointInTimeStore
from unittest.mock import patch

@pytest.fixture
def mock_store(tmp_path):
    # Create fake data
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    merchants = pd.DataFrame([{"merchant_id": "M1"}, {"merchant_id": "M2"}])
    
    transactions = pd.DataFrame([
        {"transaction_id": "T1", "merchant_id": "M1", "timestamp": "2024-01-15 12:00:00", "amount": 100},
        {"transaction_id": "T2", "merchant_id": "M1", "timestamp": "2024-02-15 12:00:00", "amount": 200},
        {"transaction_id": "T3", "merchant_id": "M1", "timestamp": "2024-03-15 12:00:00", "amount": 300},
    ])
    
    relationships = pd.DataFrame([
        {"merchant_id": "M1", "entity_type": "device", "entity_id": "D1", "start_time": "2024-01-01", "end_time": "2024-12-31"},
        {"merchant_id": "M2", "entity_type": "device", "entity_id": "D1", "start_time": "2024-03-01", "end_time": "2024-12-31"}
    ])
    
    merchants.to_csv(data_dir / "merchant_labels.csv", index=False)
    transactions.to_csv(data_dir / "transactions.csv", index=False)
    relationships.to_csv(data_dir / "relationships.csv", index=False)
    
    return PointInTimeStore(data_dir)

def test_store_excludes_future_transactions(mock_store):
    scoring_ts = "2024-01-31 23:59:59"
    
    tx = mock_store.get_merchant_transactions("M1", scoring_ts)
    
    # Should only contain T1 (Day 15)
    assert len(tx) == 1
    assert tx.iloc[0]["transaction_id"] == "T1"
    
    scoring_ts2 = "2024-02-28 23:59:59"
    tx2 = mock_store.get_merchant_transactions("M1", scoring_ts2)
    assert len(tx2) == 2
    
def test_store_excludes_future_relationships(mock_store):
    scoring_ts = "2024-02-15 23:59:59"
    
    rels = mock_store.get_active_relationships("M1", scoring_ts)
    assert len(rels) == 1
    
    # M2's relationship starts in March, so at Feb 15, the network subgraph for M1 should NOT see M2
    m, tx, subgraph_rels = mock_store.get_network_subgraph("M1", scoring_ts)
    
    assert "M1" in m["merchant_id"].values
    assert "M2" not in m["merchant_id"].values
    
def test_network_subgraph_respects_time(mock_store):
    scoring_ts = "2024-03-15 23:59:59"
    
    # At March 15, M2's relationship has started (March 1)
    m, tx, subgraph_rels = mock_store.get_network_subgraph("M1", scoring_ts)
    
    assert "M1" in m["merchant_id"].values
    assert "M2" in m["merchant_id"].values
    
def test_empty_results_handled_safely(mock_store):
    scoring_ts = "2023-01-01 00:00:00"
    m, tx, rels = mock_store.get_network_subgraph("M1", scoring_ts)
    assert len(tx) == 0
    assert len(rels) == 0
