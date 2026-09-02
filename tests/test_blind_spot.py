"""Tests for blind-spot detection module."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

from src.monitoring.blind_spot import (
    BlindSpotAnalyzer,
    BlindSpotReport,
    compute_psi,
    compute_ks,
    reconstruct_phase4b_splits,
)


# ---------------------------------------------------------------------------
# PSI / KS unit tests
# ---------------------------------------------------------------------------

def test_psi_identical_distributions():
    """Identical distributions should yield PSI near zero."""
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, size=1000)
    psi = compute_psi(ref, ref.copy())
    assert psi < 0.01

def test_psi_shifted_distribution():
    """A large mean shift should yield PSI > 0.2."""
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, size=1000)
    shifted = rng.normal(3, 1, size=1000)
    psi = compute_psi(ref, shifted)
    assert psi > 0.2

def test_ks_identical():
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, size=500)
    stat, pval = compute_ks(ref, ref.copy())
    assert stat == 0.0
    assert pval >= 0.05

def test_ks_different():
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, size=500)
    different = rng.normal(5, 1, size=500)
    stat, pval = compute_ks(ref, different)
    assert stat > 0.5
    assert pval < 0.01


# ---------------------------------------------------------------------------
# Split reconstruction test
# ---------------------------------------------------------------------------

def test_split_reconstruction_matches_metadata():
    """Verify that the reconstructed split sizes match the serialized model metadata."""
    idx_train, idx_val, idx_test, merged = reconstruct_phase4b_splits()
    assert len(idx_train) == 3499
    assert len(idx_val) == 751
    assert len(idx_test) == 750
    # No overlap
    assert len(set(idx_train) & set(idx_val)) == 0
    assert len(set(idx_train) & set(idx_test)) == 0
    assert len(set(idx_val) & set(idx_test)) == 0


# ---------------------------------------------------------------------------
# Analyzer tests using mock engine
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_analyzer():
    """Build an analyzer with controlled synthetic data."""
    engine = MagicMock()
    engine.threshold = 0.5

    # 10 merchants: 4 mules (2 TYPE_A, 2 TYPE_B), 6 benign
    features_df = pd.DataFrame({
        "merchant_id": [f"M{i}" for i in range(10)],
        "volume_delta_t1_t2": np.random.default_rng(1).normal(0, 1, 10),
        "volume_delta_t2_t3": np.random.default_rng(2).normal(0, 1, 10),
        "refund_delta_t1_t2": np.zeros(10),
        "refund_delta_t2_t3": np.zeros(10),
        "network_growth_t1_t2": np.zeros(10),
        "network_growth_t2_t3": np.zeros(10),
        "device_churn_t1_t2": np.zeros(10),
        "device_churn_t2_t3": np.zeros(10),
        "ip_churn_t1_t2": np.zeros(10),
        "ip_churn_t2_t3": np.zeros(10),
        "volume_static_t3": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    })

    labels = pd.DataFrame({
        "merchant_id": [f"M{i}" for i in range(10)],
        "is_mule": [1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        "mule_type": ["TYPE_A", "TYPE_A", "TYPE_B", "TYPE_B", "", "", "", "", "", ""],
        "network_id": ["N1", "N1", "N2", "N2", "", "", "", "", "", ""],
    })

    networks = pd.DataFrame({
        "network_id": ["N1", "N2"],
        "primary_mule_type": ["TYPE_A", "TYPE_B"],
        "merchant_count": [2, 2],
    })

    # Simulate model predictions:
    #   M0 (mule) -> detected (prob 0.8)
    #   M1 (mule) -> detected (prob 0.7)
    #   M2 (mule) -> MISSED  (prob 0.2)   <-- FN
    #   M3 (mule) -> MISSED  (prob 0.1)   <-- FN
    #   M4-M9 (benign) -> correct (prob 0.1)
    probs = np.array([[0.2, 0.8], [0.3, 0.7], [0.8, 0.2], [0.9, 0.1],
                       [0.9, 0.1], [0.9, 0.1], [0.9, 0.1], [0.9, 0.1],
                       [0.9, 0.1], [0.9, 0.1]])
    engine.model = MagicMock()
    engine.model.predict_proba = MagicMock(return_value=probs)

    analyzer = BlindSpotAnalyzer(
        engine=engine,
        labels=labels,
        networks=networks,
        features_df=features_df,
        scoring_timestamp="2026-04-01",
    )
    return analyzer


def test_global_metrics_computed(mock_analyzer):
    scored = mock_analyzer._build_scored_df()
    metrics = mock_analyzer.compute_global_metrics(scored)
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert metrics["recall"] == 0.5  # 2 out of 4 mules detected
    assert metrics["precision"] == 1.0  # no false positives


def test_fn_concentration_detected(mock_analyzer):
    """All FNs should be in TYPE_B — that segment should be flagged."""
    scored = mock_analyzer._build_scored_df()
    fn_conc = mock_analyzer.detect_fn_concentration(scored)
    type_b = [r for r in fn_conc if r["segment_value"] == "TYPE_B"]
    assert len(type_b) == 1
    assert type_b[0]["fn_count"] == 2
    assert type_b[0]["fn_rate"] == 1.0  # 100% of TYPE_B missed
    assert type_b[0]["concentrated"] is True


def test_no_false_alert_on_balanced_fn():
    """When FNs are evenly distributed, no segment should be flagged."""
    engine = MagicMock()
    engine.threshold = 0.5
    # 4 mules, all missed (balanced between 2 types)
    probs = np.array([[0.9, 0.1]] * 4 + [[0.9, 0.1]] * 4)
    engine.model = MagicMock()
    engine.model.predict_proba = MagicMock(return_value=probs)

    features_df = pd.DataFrame({
        "merchant_id": [f"M{i}" for i in range(8)],
        **{col: np.zeros(8) for col in BlindSpotAnalyzer.FEATURE_COLS},
    })
    labels = pd.DataFrame({
        "merchant_id": [f"M{i}" for i in range(8)],
        "is_mule": [1, 1, 1, 1, 0, 0, 0, 0],
        "mule_type": ["TYPE_A", "TYPE_B", "TYPE_A", "TYPE_B", "", "", "", ""],
        "network_id": ["N1", "N2", "N1", "N2", "", "", "", ""],
    })

    analyzer = BlindSpotAnalyzer(
        engine=engine, labels=labels, networks=pd.DataFrame(),
        features_df=features_df, scoring_timestamp="2026-04-01",
    )
    scored = analyzer._build_scored_df()
    fn_conc = analyzer.detect_fn_concentration(scored)
    concentrated_flags = [r for r in fn_conc if r["concentrated"]]
    assert len(concentrated_flags) == 0


def test_uses_frozen_threshold(mock_analyzer):
    """Assert the analyzer uses the engine's serialized threshold, not a recomputed one."""
    scored = mock_analyzer._build_scored_df()
    # Threshold is 0.5 (set on mock), so merchant M2 (prob=0.2) should NOT be flagged
    m2 = scored[scored["merchant_id"] == "M2"]
    assert m2.iloc[0]["predicted_label"] == 0  # below 0.5 threshold


def test_report_serialization(tmp_path):
    """BlindSpotReport can round-trip through JSON."""
    report = BlindSpotReport(
        scoring_timestamp="2026-04-01",
        global_metrics={"recall": 0.5, "precision": 1.0},
        blind_spots=[{"type": "TEST", "severity": "LOW", "description": "test"}],
    )
    path = tmp_path / "report.json"
    report.save(path)
    loaded = BlindSpotReport.load(path)
    assert loaded.scoring_timestamp == "2026-04-01"
    assert loaded.global_metrics["recall"] == 0.5
    assert len(loaded.blind_spots) == 1


# ---------------------------------------------------------------------------
# Integration test with the real frozen model
# ---------------------------------------------------------------------------

def test_end_to_end_blind_spot_analysis():
    """Run the full analyzer on the real synthetic data."""
    from src.inference.scorer import InferenceEngine

    engine = InferenceEngine.get_instance()
    features_df = pd.read_csv("data/synthetic_v2/evolution_features.csv")
    labels = pd.read_csv("data/synthetic_v2/merchant_labels.csv")
    networks = pd.read_csv("data/synthetic_v2/mule_networks.csv")
    merchants_path = Path("data/synthetic_v2/merchants.csv")
    merchants_df = pd.read_csv(merchants_path) if merchants_path.exists() else None

    analyzer = BlindSpotAnalyzer(
        engine=engine,
        labels=labels,
        networks=networks,
        features_df=features_df,
        merchants_df=merchants_df,
        scoring_timestamp="2026-04-01",
    )
    report = analyzer.run_full_analysis()

    # Structural validity
    assert report.scoring_timestamp == "2026-04-01"
    assert "recall" in report.global_metrics
    assert "recall" in report.baseline_metrics
    assert report.baseline_metrics["split"] == "validation"
    assert report.baseline_metrics["split_size"] == 751
    assert isinstance(report.recall_degradation, dict)
    assert len(report.segment_metrics) > 0
    assert len(report.feature_drift) == 10  # one per model feature


from pathlib import Path
