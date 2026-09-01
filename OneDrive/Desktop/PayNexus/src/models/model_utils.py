"""Machine learning model utilities and factory for MuleHunter."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Attempt XGBoost import; fallback gracefully to Scikit-Learn Gradient Boosting
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

from sklearn.ensemble import HistGradientBoostingClassifier, GradientBoostingClassifier


BEHAVIORAL_FEATURE_SUBSET = [
    "merchant_age_days",
    "kyc_verified",
    "kyc_pending",
    "kyc_limited",
    "transaction_count",
    "total_transaction_volume",
    "average_transaction_amount",
    "median_transaction_amount",
    "transaction_amount_std",
    "unique_customer_count",
    "unique_device_count",
    "unique_ip_count",
    "active_days_count",
    "success_rate",
    "failure_rate",
    "refund_rate",
    "refund_count",
    "refund_volume",
    "refund_amount_ratio",
    "unique_settlement_account_count",
    "settlement_count",
    "total_settlement_volume",
    "pm_share_upi",
    "pm_share_card",
    "pm_share_netbanking",
    "pm_share_wallet",
    "avg_tx_per_customer",
    "avg_tx_per_device",
    "avg_tx_per_ip",
    "transaction_velocity",
    "average_daily_volume",
    "volume_growth",
]

NETWORK_FEATURE_SUBSET = [
    "shared_device_count",
    "shared_ip_count",
    "shared_customer_count",
    "shared_settlement_count",
    "connected_merchant_count",
    "merchant_degree",
    "weighted_network_degree",
    "network_size",
    "network_density",
    "clustering_coefficient",
    "pagerank_score",
    "betweenness_centrality",
]

TEMPORAL_FEATURE_SUBSET = [
    "transaction_time_concentration",
    "night_tx_share",
    "business_hours_tx_share",
    "evening_tx_share",
    "weekend_tx_share",
    "active_days_ratio",
    "transaction_burst_score",
    "volume_spike_score",
    "daily_volume_cv",
    "coordinated_activity_score",
]

COORDINATION_FEATURE_SUBSET = [
    "avg_ip_rarity",
    "avg_device_rarity",
    "avg_customer_rarity",
    "avg_ip_frequency",
    "avg_device_frequency",
    "shared_ip_volume_ratio",
    "shared_device_volume_ratio",
    "shared_customer_volume_ratio",
    "volume_burstiness",
]

PEER_FEATURE_SUBSET = [
    "transaction_count_zscore_vs_peers",
    "total_transaction_volume_zscore_vs_peers",
    "average_transaction_amount_zscore_vs_peers",
    "refund_rate_zscore_vs_peers",
    "failure_rate_zscore_vs_peers",
    "unique_customer_count_zscore_vs_peers",
]


def create_classifier(seed: int = 42, use_xgboost_if_available: bool = True) -> Any:
    """Factory to instantiate tree-based classification model (XGBoost or GradientBoosting)."""
    if HAS_XGBOOST and use_xgboost_if_available:
        return xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=seed,
            eval_metric="logloss",
        )
    else:
        return GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            random_state=seed,
        )


def find_optimal_threshold(y_true: np.ndarray, y_probs: np.ndarray) -> float:
    """Find probability decision threshold that maximizes F1 score on validation set."""
    if len(np.unique(y_true)) < 2:
        return 0.5

    precisions, recalls, thresholds = precision_recall_curve(y_true, y_probs)
    f1_scores = []
    for p, r in zip(precisions[:-1], recalls[:-1]):
        if p + r > 0:
            f1 = 2.0 * (p * r) / (p + r)
        else:
            f1 = 0.0
        f1_scores.append(f1)

    if not f1_scores or len(thresholds) == 0:
        return 0.5

    max_f1 = np.max(f1_scores)
    if max_f1 <= 0.0:
        return 0.5

    best_indices = np.where(np.isclose(f1_scores, max_f1))[0]
    # Pick the index among optimal F1s that has highest precision to reduce false positives
    best_idx = best_indices[np.argmax(precisions[best_indices])]
    best_threshold = float(thresholds[best_idx])
    return float(np.clip(best_threshold, 0.05, 0.95))


def compute_risk_score(probabilities: np.ndarray) -> np.ndarray:
    """Calibrate probabilities into a clean 0 to 100 risk score integer."""
    scaled = np.clip(probabilities * 100.0, 0.0, 100.0)
    return np.round(scaled, 1)


def evaluate_predictions(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Calculate standard binary classification evaluation metrics."""
    y_pred = (y_probs >= threshold).astype(int)

    # ROC AUC & PR AUC
    if len(np.unique(y_true)) >= 2:
        roc_auc = float(roc_auc_score(y_true, y_probs))
        pr_auc = float(average_precision_score(y_true, y_probs))
    else:
        roc_auc = 0.0
        pr_auc = 0.0

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "false_positive_rate": round(fpr, 4),
        "threshold": round(threshold, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
    }


def extract_feature_importances(model: Any, feature_names: list[str]) -> pd.DataFrame:
    """Extract normalized feature importances from tree-based model."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        importances = np.zeros(len(feature_names))

    df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    total = df["importance"].sum()
    if total > 0:
        df["importance_share"] = df["importance"] / total
    else:
        df["importance_share"] = 0.0

    return df
