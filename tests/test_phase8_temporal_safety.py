import pytest
import pandas as pd
from src.inference.scorer import score_merchant

@pytest.fixture
def base_data():
    merchants = pd.DataFrame([{"merchant_id": "M_TEST"}])
    
    transactions = pd.DataFrame([
        {"transaction_id": "T1", "merchant_id": "M_TEST", "amount": 100.0, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-01-15")}
    ])
    
    relationships = pd.DataFrame([
        {"merchant_id": "M_TEST", "entity_type": "device", "entity_id": "D1", "start_time": pd.Timestamp("2024-01-01"), "end_time": pd.Timestamp("2024-12-31")}
    ])
    
    return merchants, transactions, relationships

def test_temporal_safety_future_transactions(base_data):
    """Verify that adding future transactions does NOT change the historical point-in-time score."""
    merchants, transactions, relationships = base_data
    
    scoring_timestamp = "2024-01-31"
    
    # 1. Score with base data
    base_result = score_merchant(
        merchant_id="M_TEST", 
        scoring_timestamp=scoring_timestamp, 
        merchants=merchants, 
        transactions=transactions, 
        relationships=relationships
    )
    
    # 2. Add adversarial FUTURE data
    adversarial_tx = pd.DataFrame([
        {"transaction_id": "T2", "merchant_id": "M_TEST", "amount": 99999.0, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-02-15")}
    ])
    adversarial_transactions = pd.concat([transactions, adversarial_tx], ignore_index=True)
    
    # 3. Score with adversarial future data at the historical timestamp
    adversarial_result = score_merchant(
        merchant_id="M_TEST", 
        scoring_timestamp=scoring_timestamp, 
        merchants=merchants, 
        transactions=adversarial_transactions, 
        relationships=relationships
    )
    
    # The results must be perfectly mathematically identical
    assert base_result["risk_score"] == adversarial_result["risk_score"]
    assert base_result["probability"] == adversarial_result["probability"]
    assert base_result["evidence_features"] == adversarial_result["evidence_features"]

def test_temporal_safety_future_relationships(base_data):
    """Verify that adding future relationships does NOT change the historical point-in-time network features."""
    merchants, transactions, relationships = base_data
    
    scoring_timestamp = "2024-01-31"
    
    base_result = score_merchant(
        merchant_id="M_TEST", 
        scoring_timestamp=scoring_timestamp, 
        merchants=merchants, 
        transactions=transactions, 
        relationships=relationships
    )
    
    # Add an adversarial future relationship that connects them to a massive mule ring (simulated)
    adversarial_rel = pd.DataFrame([
        {"merchant_id": "M_TEST", "entity_type": "device", "entity_id": "MULE_DEVICE_99", "start_time": pd.Timestamp("2024-03-01"), "end_time": pd.Timestamp("2024-12-31")}
    ])
    adversarial_relationships = pd.concat([relationships, adversarial_rel], ignore_index=True)
    
    adversarial_result = score_merchant(
        merchant_id="M_TEST", 
        scoring_timestamp=scoring_timestamp, 
        merchants=merchants, 
        transactions=transactions, 
        relationships=adversarial_relationships
    )
    
    assert base_result["risk_score"] == adversarial_result["risk_score"]
    assert base_result["evidence_features"] == adversarial_result["evidence_features"]
