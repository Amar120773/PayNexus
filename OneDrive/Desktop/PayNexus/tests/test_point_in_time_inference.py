import pandas as pd
import pytest
from src.features_v2.evolution_features import extract_evolution_features

@pytest.fixture
def point_in_time_data():
    merchants = pd.DataFrame([{"merchant_id": "M1"}])
    transactions = pd.DataFrame([
        # Day 1-30 (T1)
        {"merchant_id": "M1", "amount": 100, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-01-15")},
        # Day 31-60 (T2)
        {"merchant_id": "M1", "amount": 200, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-02-15")},
        # Day 61-90 (T3)
        {"merchant_id": "M1", "amount": 300, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-03-15")}
    ])
    relationships = pd.DataFrame([
        {"merchant_id": "M1", "entity_type": "device", "entity_id": "D1", "start_time": pd.Timestamp("2024-01-15"), "end_time": pd.Timestamp("2024-04-30")},
    ])
    return merchants, transactions, relationships

def test_evolution_windows_correctly_aligned(point_in_time_data):
    merchants, transactions, relationships = point_in_time_data
    
    # Score at end of Day 90
    scoring_timestamp = "2024-03-31"
    
    features = extract_evolution_features(
        merchants, transactions, relationships, scoring_timestamp, ["M1"]
    )
    
    row = features.iloc[0]
    
    # T3 is Day 61-90 (volume 300)
    # T2 is Day 31-60 (volume 200)
    # T1 is Day 1-30 (volume 100)
    
    # volume_delta_t2_t3 = T3 - T2 = 300 - 200 = 100
    assert row["volume_delta_t2_t3"] == 100
    
    # volume_delta_t1_t2 = T2 - T1 = 200 - 100 = 100
    assert row["volume_delta_t1_t2"] == 100
    
    # Static T3 = 300
    assert row["volume_static_t3"] == 300

def test_point_in_time_guarantee(point_in_time_data):
    merchants, transactions, relationships = point_in_time_data
    
    # If we score at Day 60, T3 should be Day 31-60 (volume 200)
    scoring_timestamp = "2024-03-01"
    
    features = extract_evolution_features(
        merchants, transactions, relationships, scoring_timestamp, ["M1"]
    )
    
    row = features.iloc[0]
    
    # volume_static_t3 should be 200 (Day 31-60)
    assert row["volume_static_t3"] == 200
    
    # volume_delta_t2_t3 = T3(200) - T2(100) = 100
    assert row["volume_delta_t2_t3"] == 100
