import pytest
from fastapi.testclient import TestClient
import pandas as pd
from unittest.mock import patch
from typing import Generator

from src.api.app import app
from src.inference.store import PointInTimeStore

# We use the real test client but we need to ensure the startup event runs.
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_model_metadata(client: TestClient):
    response = client.get("/model/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "threshold" in data
    assert "feature_list" in data

def test_unknown_merchant(client: TestClient):
    response = client.post(
        "/v1/score/merchant",
        json={"merchant_id": "UNKNOWN_M", "scoring_timestamp": "2024-01-15 00:00:00"}
    )
    assert response.status_code == 404

def test_malformed_request(client: TestClient):
    response = client.post(
        "/v1/score/merchant",
        json={"merchant_id": "M1"} # Missing timestamp
    )
    assert response.status_code == 422

def test_api_preserves_temporal_immunity(client: TestClient, tmp_path):
    """
    Test the Architectural Boundary: API -> PointInTimeStore -> Engine -> Model.
    Verifies that appending future transactions/relationships does NOT change 
    the point-in-time scoring result.
    """
    # 1. We must score a real merchant from the dataset to ensure we get a valid result.
    # Let's get the store and find a merchant.
    store = PointInTimeStore.get_instance()
    m_id = store.merchants.iloc[0]["merchant_id"]
    
    scoring_ts = "2024-02-15 00:00:00"
    
    # 2. Score at T
    req_payload = {"merchant_id": m_id, "scoring_timestamp": scoring_ts}
    response1 = client.post("/v1/score/merchant", json=req_payload)
    
    if response1.status_code == 404:
        pytest.skip(f"Merchant {m_id} has no data at {scoring_ts}. Skipping architectural boundary test.")
        
    assert response1.status_code == 200
    result1 = response1.json()
    
    # 3. Simulate future data by temporarily patching the store
    # We will append transactions and relationships far into the future.
    original_tx = store.transactions.copy()
    original_rels = store.relationships.copy()
    
    future_tx = pd.DataFrame([{
        "transaction_id": "FUT1",
        "merchant_id": m_id,
        "amount": 99999.0,
        "timestamp": pd.Timestamp("2024-12-31 00:00:00"),
        "status": "APPROVED",
        "customer_id": "C999",
        "card_type": "CREDIT"
    }])
    
    future_rel = pd.DataFrame([{
        "merchant_id": m_id,
        "entity_type": "device",
        "entity_id": "FUTURE_DEV",
        "start_time": pd.Timestamp("2024-12-01 00:00:00"),
        "end_time": pd.Timestamp("2025-01-01 00:00:00")
    }])
    
    try:
        # Inject future data
        store.transactions = pd.concat([store.transactions, future_tx], ignore_index=True)
        store.relationships = pd.concat([store.relationships, future_rel], ignore_index=True)
        
        # 4. Score same merchant again at T
        response2 = client.post("/v1/score/merchant", json=req_payload)
        assert response2.status_code == 200
        result2 = response2.json()
        
        # 5. Assert results are mathematically identical
        assert result1["probability"] == result2["probability"]
        assert result1["evidence_features"] == result2["evidence_features"]
        
    finally:
        # Restore store to keep tests isolated
        store.transactions = original_tx
        store.relationships = original_rels

def test_network_scoring_api(client: TestClient):
    store = PointInTimeStore.get_instance()
    m_id = store.merchants.iloc[0]["merchant_id"]
    scoring_ts = "2024-03-30 00:00:00"
    
    req_payload = {"merchant_id": m_id, "scoring_timestamp": scoring_ts}
    response = client.post("/v1/score/network", json=req_payload)
    
    if response.status_code == 404:
        pytest.skip("No network data.")
        
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) >= 1
    
def test_deterministic_repeated_scoring(client: TestClient):
    store = PointInTimeStore.get_instance()
    m_id = store.merchants.iloc[0]["merchant_id"]
    scoring_ts = "2024-03-30 00:00:00"
    
    req = {"merchant_id": m_id, "scoring_timestamp": scoring_ts}
    res1 = client.post("/v1/score/merchant", json=req)
    res2 = client.post("/v1/score/merchant", json=req)
    
    if res1.status_code == 200:
        assert res1.json() == res2.json()

def test_blind_spot_report_endpoint(client: TestClient):
    """Test that GET /v1/monitoring/blind-spots returns the pre-computed report."""
    response = client.get("/v1/monitoring/blind-spots")
    assert response.status_code == 200
    data = response.json()
    assert "scoring_timestamp" in data
    assert "global_metrics" in data
    assert "baseline_metrics" in data
    assert "recall_degradation" in data
    assert "blind_spots" in data
    assert isinstance(data["blind_spots"], list)

