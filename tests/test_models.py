"""Tests for Baseline and MuleHunter model training, scoring, and predictions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset
from src.evaluation.network_split import generate_network_splits
from src.features.build_features import build_master_feature_table
from src.graph.build_graph import build_projected_merchant_graph
from src.models.baseline import train_baseline_model
from src.models.model_utils import (
    BEHAVIORAL_FEATURE_SUBSET,
    NETWORK_FEATURE_SUBSET,
    TEMPORAL_FEATURE_SUBSET,
    compute_risk_score,
    find_optimal_threshold,
)
from src.models.mulehunter import train_mulehunter_model


@pytest.fixture
def dataset_and_features() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = SyntheticDataConfig(
        merchants=60,
        transactions=600,
        customers=150,
        devices=80,
        ips=80,
        settlement_accounts=60,
        mule_networks=3,
        period_days=60,
        seed=102,
    )
    dataset = generate_dataset(config)
    proj_graph = build_projected_merchant_graph(dataset)
    labels_df = dataset["merchant_labels"]
    splits_df = generate_network_splits(
        labels_df=labels_df,
        merchants_df=dataset["merchants"],
        projected_graph=proj_graph,
        seed=102,
    )
    features_df, labels_df = build_master_feature_table(dataset, splits_df)
    return features_df, labels_df, splits_df


def test_baseline_model_training_and_predictions(
    dataset_and_features: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    features_df, labels_df, splits_df = dataset_and_features

    model, metrics, preds_df, threshold = train_baseline_model(
        features_df=features_df,
        labels_df=labels_df,
        splits_df=splits_df,
        seed=42,
    )

    assert len(preds_df) == len(features_df)
    assert set(preds_df.columns) == {
        "merchant_id",
        "split",
        "is_mule",
        "mule_probability",
        "risk_score",
        "predicted_label",
    }
    assert (preds_df["mule_probability"].between(0.0, 1.0)).all()
    assert (preds_df["risk_score"].between(0.0, 100.0)).all()
    assert set(preds_df["predicted_label"].unique()).issubset({0, 1})

    assert "f1" in metrics
    assert "roc_auc" in metrics
    assert "precision" in metrics
    assert "recall" in metrics


def test_mulehunter_model_training_and_feature_importance(
    dataset_and_features: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    features_df, labels_df, splits_df = dataset_and_features

    model, metrics, preds_df, threshold, importance_df = train_mulehunter_model(
        features_df=features_df,
        labels_df=labels_df,
        splits_df=splits_df,
        seed=42,
    )

    assert len(preds_df) == len(features_df)
    assert len(importance_df) > 0
    assert "feature" in importance_df.columns
    assert "importance" in importance_df.columns
    assert "importance_share" in importance_df.columns
    assert importance_df["importance_share"].sum() >= 0.0


def test_threshold_optimization_and_risk_scoring() -> None:
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_probs = np.array([0.1, 0.2, 0.15, 0.3, 0.7, 0.85, 0.9, 0.6])

    threshold = find_optimal_threshold(y_true, y_probs)
    assert 0.10 <= threshold <= 0.90

    risk_scores = compute_risk_score(y_probs)
    assert len(risk_scores) == len(y_probs)
    assert (risk_scores >= 0.0).all() and (risk_scores <= 100.0).all()
