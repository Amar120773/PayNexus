import pandas as pd
import pytest
from src.inference.scorer import score_merchant, score_network

@pytest.fixture
def dummy_data():
    merchants = pd.DataFrame([{"merchant_id": "M1"}, {"merchant_id": "M2"}])
    transactions = pd.DataFrame([
        {"merchant_id": "M1", "amount": 100, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-06-01")},
        {"merchant_id": "M2", "amount": 200, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-06-05")}
    ])
    relationships = pd.DataFrame([
        {"merchant_id": "M1", "entity_type": "device", "entity_id": "D1", "start_time": pd.Timestamp("2024-05-01"), "end_time": pd.Timestamp("2024-12-31")},
        {"merchant_id": "M2", "entity_type": "device", "entity_id": "D1", "start_time": pd.Timestamp("2024-05-01"), "end_time": pd.Timestamp("2024-12-31")}
    ])
    return merchants, transactions, relationships

def test_score_merchant_returns_structured_object(dummy_data):
    merchants, transactions, relationships = dummy_data
    scoring_timestamp = "2024-07-01"
    
    result = score_merchant("M1", scoring_timestamp, merchants, transactions, relationships)
    
    expected_keys = [
        "merchant_id", "scoring_timestamp", "risk_score", "probability",
        "risk_band", "behavioral_risk", "network_risk", "evidence_features"
    ]
    for key in expected_keys:
        assert key in result
        
    assert result["merchant_id"] == "M1"
    assert result["scoring_timestamp"] == scoring_timestamp
    assert isinstance(result["risk_score"], float)

def test_score_network_returns_list_of_objects(dummy_data):
    merchants, transactions, relationships = dummy_data
    scoring_timestamp = "2024-07-01"
    
    results = score_network("M1", scoring_timestamp, merchants, transactions, relationships)
    
    assert isinstance(results, list)
    assert len(results) == 2  # M1 and M2 share device D1
    
    merchant_ids = [r["merchant_id"] for r in results]
    assert "M1" in merchant_ids
    assert "M2" in merchant_ids
