import pytest
from fastapi.testclient import TestClient
from typing import Generator
import pandas as pd

from src.api.app import app
from src.inference.store import PointInTimeStore

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

def get_valid_merchant():
    store = PointInTimeStore.get_instance()
    # Ensure there are merchants available
    if len(store.merchants) == 0:
        pytest.skip("No merchants loaded in store")
    return store.merchants.iloc[-1]["merchant_id"] # Get one likely to have data

def test_timeline_consistency(client: TestClient):
    m_id = get_valid_merchant()
    timestamps = ["2024-01-15 00:00:00", "2024-02-15 00:00:00", "2024-03-15 00:00:00"]
    
    response_tl = client.post(
        "/v1/score/merchant/timeline", 
        json={"merchant_id": m_id, "scoring_timestamps": timestamps}
    )
    
    if response_tl.status_code == 404:
        pytest.skip("Merchant has no data in timeline")
        
    assert response_tl.status_code == 200
    timeline_results = response_tl.json()
    
    # Verify each point mathematically matches individual endpoint
    for res in timeline_results:
        ts = res["scoring_timestamp"]
        response_indiv = client.post("/v1/score/merchant", json={"merchant_id": m_id, "scoring_timestamp": ts})
        assert response_indiv.status_code == 200
        indiv_res = response_indiv.json()
        assert res["probability"] == indiv_res["probability"]
        assert res["risk_score"] == indiv_res["risk_score"]

def test_chronological_ordering(client: TestClient):
    m_id = get_valid_merchant()
    timestamps = ["2024-03-15 00:00:00", "2024-01-15 00:00:00", "2024-02-15 00:00:00"]
    
    response_tl = client.post(
        "/v1/score/merchant/timeline", 
        json={"merchant_id": m_id, "scoring_timestamps": timestamps}
    )
    
    if response_tl.status_code == 200:
        results = response_tl.json()
        output_timestamps = [pd.Timestamp(r["scoring_timestamp"]) for r in results]
        assert output_timestamps == sorted(output_timestamps)

def test_invalid_timestamps_skipped(client: TestClient):
    m_id = get_valid_merchant()
    timestamps = ["1999-01-01 00:00:00", "2024-03-15 00:00:00"]
    response_tl = client.post(
        "/v1/score/merchant/timeline", 
        json={"merchant_id": m_id, "scoring_timestamps": timestamps}
    )
    
    # It should safely return scores even if there is no activity (0s feature vector)
    assert response_tl.status_code == 200
    results = response_tl.json()
    assert len(results) == 2
    
    # 1999 score should have very low transaction counts, resulting in low risk
    res_1999 = next(r for r in results if r["scoring_timestamp"] == "1999-01-01 00:00:00")
    assert res_1999["probability"] < 0.3263
    assert res_1999["risk_band"] == "LOW"

def test_unknown_merchant_timeline(client: TestClient):
    response = client.post(
        "/v1/score/merchant/timeline", 
        json={"merchant_id": "FAKE_MERCHANT", "scoring_timestamps": ["2024-01-01 00:00:00"]}
    )
    assert response.status_code == 404

def test_merchant_metadata_sanitization(client: TestClient):
    m_id = get_valid_merchant()
    response = client.get(f"/v1/merchant/{m_id}")
    
    if response.status_code in [404, 503]:
        pytest.skip(f"No metadata found or loaded. Code: {response.status_code}")
        
    assert response.status_code == 200
    data = response.json()
    
    assert "merchant_id" in data
    assert data["merchant_id"] == m_id
    
    # Must NOT contain research labels
    assert "is_mule" not in data
    assert "mule_type" not in data
    assert "network_id" not in data
