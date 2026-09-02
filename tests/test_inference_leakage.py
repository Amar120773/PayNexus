import pandas as pd
import pytest
from src.inference.scorer import score_merchant
from src.features_v2.evolution_features import extract_evolution_features

@pytest.fixture
def temporal_data():
    merchants = pd.DataFrame([{"merchant_id": "M1"}, {"merchant_id": "M2"}])
    
    # Day 30 is 2024-01-31
    # Day 60 is 2024-03-01
    # Day 90 is 2024-03-31
    
    transactions = pd.DataFrame([
        # Day 1-30
        {"merchant_id": "M1", "amount": 100, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-01-15")},
        # Day 31-60
        {"merchant_id": "M1", "amount": 200, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-02-15")},
        # Day 61-90
        {"merchant_id": "M1", "amount": 300, "status": "COMPLETED", "timestamp": pd.Timestamp("2024-03-15")}
    ])
    
    relationships = pd.DataFrame([
        # Past relationship
        {"merchant_id": "M1", "entity_type": "device", "entity_id": "D1", "start_time": pd.Timestamp("2024-01-15"), "end_time": pd.Timestamp("2024-04-30")},
        # Future relationship (created day 70)
        {"merchant_id": "M1", "entity_type": "ip", "entity_id": "IP1", "start_time": pd.Timestamp("2024-03-10"), "end_time": pd.Timestamp("2024-04-30")},
        {"merchant_id": "M2", "entity_type": "ip", "entity_id": "IP1", "start_time": pd.Timestamp("2024-03-10"), "end_time": pd.Timestamp("2024-04-30")}
    ])
    
    return merchants, transactions, relationships

def test_leakage_a_day_30(temporal_data):
    """TEST A: Score merchant at Day 30. Add Day-31+ records. Score again. IDENTICAL."""
    merchants, transactions, relationships = temporal_data
    scoring_timestamp = "2024-01-31"
    
    # Only Day 1-30 records
    tx_subset = transactions[transactions["timestamp"] <= pd.Timestamp(scoring_timestamp)]
    rels_subset = relationships[relationships["start_time"] <= pd.Timestamp(scoring_timestamp)]
    
    res1 = score_merchant("M1", scoring_timestamp, merchants, tx_subset, rels_subset)
    
    # Full records
    res2 = score_merchant("M1", scoring_timestamp, merchants, transactions, relationships)
    
    assert res1["evidence_features"] == res2["evidence_features"]

def test_leakage_b_day_60(temporal_data):
    """TEST B: Score merchant at Day 60. Add Day-61+ records. IDENTICAL."""
    merchants, transactions, relationships = temporal_data
    scoring_timestamp = "2024-03-01"
    
    tx_subset = transactions[transactions["timestamp"] <= pd.Timestamp(scoring_timestamp)]
    rels_subset = relationships[relationships["start_time"] <= pd.Timestamp(scoring_timestamp)]
    
    res1 = score_merchant("M1", scoring_timestamp, merchants, tx_subset, rels_subset)
    res2 = score_merchant("M1", scoring_timestamp, merchants, transactions, relationships)
    
    assert res1["evidence_features"] == res2["evidence_features"]

def test_leakage_c_d_graph_construction(temporal_data):
    """TEST C & D: Graph containing future relationships do not exist in G(T)."""
    merchants, transactions, relationships = temporal_data
    scoring_timestamp = "2024-03-01" # Day 60
    
    features = extract_evolution_features(
        merchants, transactions, relationships, scoring_timestamp, ["M1"]
    )
    
    # At Day 60, IP1 relationship (created Day 70) should NOT be in the graph.
    # Therefore, M1's network size at T3 (which is Day 60) should be 0 because M1 and M2 don't share D1.
    assert features.iloc[0]["network_size_static_t3"] == 0

def test_leakage_f_labels_omitted(temporal_data):
    """TEST F: network_id, is_mule, mule_type cannot enter inference matrix."""
    merchants, transactions, relationships = temporal_data
    
    merchants_leak = merchants.copy()
    merchants_leak["is_mule"] = 1
    merchants_leak["network_id"] = "N1"
    merchants_leak["mule_type"] = "A"
    
    res = score_merchant("M1", "2024-03-31", merchants_leak, transactions, relationships)
    features = res["evidence_features"]
    
    assert "is_mule" not in features
    assert "network_id" not in features
    assert "mule_type" not in features
