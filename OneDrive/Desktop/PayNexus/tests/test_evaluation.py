"""Tests for network-level splits, ablation study, and evaluation metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset
from src.evaluation.evaluate import (
    compute_network_level_metrics,
    run_ablation_study,
)
from src.evaluation.network_split import generate_network_splits
from src.features.build_features import build_master_feature_table
from src.graph.build_graph import build_projected_merchant_graph


@pytest.fixture
def dataset_and_features() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    config = SyntheticDataConfig(
        merchants=70,
        transactions=700,
        customers=180,
        devices=90,
        ips=90,
        settlement_accounts=70,
        mule_networks=3,
        period_days=60,
        seed=103,
    )
    dataset = generate_dataset(config)
    proj_graph = build_projected_merchant_graph(dataset)
    labels_df = dataset["merchant_labels"]
    splits_df = generate_network_splits(
        labels_df=labels_df,
        merchants_df=dataset["merchants"],
        projected_graph=proj_graph,
        seed=103,
    )
    features_df, labels_df = build_master_feature_table(dataset, splits_df)
    return features_df, labels_df, splits_df, dataset


def test_network_level_split_integrity(
    dataset_and_features: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]],
) -> None:
    _, labels_df, splits_df, _ = dataset_and_features

    merged = labels_df.merge(splits_df, on="merchant_id")
    mule_merchants = merged[merged["is_mule"] == 1]

    # Crucial property: Every mule network must be strictly contained within exactly ONE split
    for net_id, group in mule_merchants.groupby("network_id"):
        split_set = set(group["split"])
        assert len(split_set) == 1, f"Network {net_id} is split across multiple partitions: {split_set}"

    # Verify all splits are non-empty
    assert (splits_df["split"] == "train").sum() > 0
    assert (splits_df["split"] == "val").sum() > 0
    assert (splits_df["split"] == "test").sum() > 0


def test_ablation_study_execution(
    dataset_and_features: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]],
) -> None:
    features_df, labels_df, splits_df, _ = dataset_and_features

    comparison_df, artifacts = run_ablation_study(
        features_df=features_df,
        labels_df=labels_df,
        splits_df=splits_df,
        seed=42,
    )

    assert len(comparison_df) == 5
    assert "Model A: Behavior Only (Baseline)" in artifacts
    assert "Model E: Behavior + Network + Peer-Relative Deviation" in artifacts
    assert "f1" in comparison_df.columns
    assert "roc_auc" in comparison_df.columns
    assert "network_detection_recall" in comparison_df.columns


def test_reproducibility_of_models(
    dataset_and_features: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]],
) -> None:
    features_df, labels_df, splits_df, _ = dataset_and_features

    comp1, _ = run_ablation_study(features_df, labels_df, splits_df, seed=42)
    comp2, _ = run_ablation_study(features_df, labels_df, splits_df, seed=42)

    pd.testing.assert_frame_equal(comp1, comp2)
