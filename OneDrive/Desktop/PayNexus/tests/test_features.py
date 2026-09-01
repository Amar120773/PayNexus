"""Tests for behavioral, network, and temporal feature extraction and leakage prevention."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset
from src.features.behavioral_features import extract_behavioral_features
from src.features.build_features import (
    audit_feature_quality,
    build_master_feature_table,
)
from src.features.network_features import extract_network_features
from src.features.temporal_features import extract_temporal_features
from src.graph.build_graph import build_projected_merchant_graph


@pytest.fixture
def sample_dataset() -> dict[str, pd.DataFrame]:
    config = SyntheticDataConfig(
        merchants=40,
        transactions=400,
        customers=100,
        devices=60,
        ips=60,
        settlement_accounts=50,
        mule_networks=2,
        period_days=60,
        seed=101,
    )
    return generate_dataset(config)


def test_behavioral_features_calculation(sample_dataset: dict[str, pd.DataFrame]) -> None:
    features = extract_behavioral_features(sample_dataset)

    assert len(features) == len(sample_dataset["merchants"])
    assert "merchant_id" in features.columns
    assert "transaction_count" in features.columns
    assert "total_transaction_volume" in features.columns
    assert "success_rate" in features.columns
    assert "failure_rate" in features.columns
    assert "refund_rate" in features.columns
    assert "transaction_velocity" in features.columns

    # No NaN or inf values
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    assert not features[numeric_cols].isna().any().any()
    assert not np.isinf(features[numeric_cols]).any().any()


def test_network_features_calculation_and_no_leakage(sample_dataset: dict[str, pd.DataFrame]) -> None:
    proj_graph = build_projected_merchant_graph(sample_dataset)
    features = extract_network_features(sample_dataset, projected_graph=proj_graph)

    assert len(features) == len(sample_dataset["merchants"])
    assert "shared_device_count" in features.columns
    assert "shared_ip_count" in features.columns
    assert "shared_customer_count" in features.columns
    assert "shared_settlement_count" in features.columns
    assert "connected_merchant_count" in features.columns
    assert "network_size" in features.columns
    assert "network_density" in features.columns

    # Verify absence of ground-truth labels
    forbidden = {"is_mule", "mule_type", "network_id", "mule_labeled_neighbors_count"}
    assert forbidden.isdisjoint(features.columns)

    # No NaN or inf values
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    assert not features[numeric_cols].isna().any().any()
    assert not np.isinf(features[numeric_cols]).any().any()


def test_temporal_features_calculation(sample_dataset: dict[str, pd.DataFrame]) -> None:
    proj_graph = build_projected_merchant_graph(sample_dataset)
    features = extract_temporal_features(sample_dataset, projected_graph=proj_graph)

    assert len(features) == len(sample_dataset["merchants"])
    assert "transaction_time_concentration" in features.columns
    assert "night_tx_share" in features.columns
    assert "weekend_tx_share" in features.columns
    assert "transaction_burst_score" in features.columns
    assert "volume_spike_score" in features.columns
    assert "coordinated_activity_score" in features.columns

    # Value ranges
    assert (features["transaction_time_concentration"].between(0.0, 1.0)).all()
    assert (features["night_tx_share"].between(0.0, 1.0)).all()
    assert (features["weekend_tx_share"].between(0.0, 1.0)).all()


def test_master_feature_table_and_leakage_audit(sample_dataset: dict[str, pd.DataFrame]) -> None:
    splits_df = pd.DataFrame([
        {"merchant_id": m, "split": "train"} for m in sample_dataset["merchants"]["merchant_id"]
    ])
    features_df, labels_df = build_master_feature_table(sample_dataset, splits_df)

    assert len(features_df) == len(sample_dataset["merchants"])
    assert len(labels_df) == len(sample_dataset["merchants"])

    # Strict leakage check
    forbidden = {"is_mule", "mule_type", "network_id"}
    assert forbidden.isdisjoint(features_df.columns)

    # Run audit
    audit_results = audit_feature_quality(features_df, labels_df)
    assert len(audit_results["missing_values"]) == 0
    assert len(audit_results["infinite_values"]) == 0
    assert audit_results["duplicate_merchants"] == 0
    assert len(audit_results["leaked_columns"]) == 0
