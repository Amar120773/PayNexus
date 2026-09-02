import pytest
from fastapi.testclient import TestClient
from typing import Generator
from src.api.app import app

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

def test_explainability_endpoint_success(client: TestClient):
    payload = {
        "merchant_id": "M00109",
        "scoring_timestamp": "2026-03-31 00:00:00"
    }
    # 1. Fetch explanation
    res = client.post("/v1/explain/merchant", json=payload)
    print(f"DEBUG RESPONSE: {res.text}")
    assert res.status_code == 200
    data = res.json()
    
    # Validation checks
    assert data["merchant_id"] == "M00109"
    assert "risk_score" in data
    assert "probability" in data
    assert "risk_band" in data
    assert "base_value" in data
    assert len(data["explanations"]) > 0
    
    first_exp = data["explanations"][0]
    assert "feature_name" in first_exp
    assert "shap_value" in first_exp
    assert "direction" in first_exp
    
    # 2. Compare against normal scoring endpoint to ensure exact match
    score_res = client.post("/v1/score/merchant", json=payload)
    assert score_res.status_code == 200
    score_data = score_res.json()
    
    assert data["probability"] == score_data["probability"]
    assert data["risk_band"] == score_data["risk_band"]
    
def test_invalid_merchant_expl(client: TestClient):
    payload = {
        "merchant_id": "INVALID",
        "scoring_timestamp": "2026-03-31 00:00:00"
    }
    res = client.post("/v1/explain/merchant", json=payload)
    assert res.status_code == 404

def test_point_in_time_safety():
    # If we score exactly when onboarding occurs, some temporal features might be 0, but it should still work
    pass
