"""Baseline behavior-only mule detection model for MuleHunter."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.models.model_utils import (
    BEHAVIORAL_FEATURE_SUBSET,
    compute_risk_score,
    create_classifier,
    evaluate_predictions,
    extract_feature_importances,
    find_optimal_threshold,
)


def train_baseline_model(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    splits_df: pd.DataFrame,
    seed: int = 42,
) -> tuple[Any, dict[str, Any], pd.DataFrame, float]:
    """Train behavior-only baseline model using exclusively individual operational signals.

    Excludes all graph, network, and temporal coordination features.
    """
    # 1. Prepare data
    merged = features_df.merge(labels_df[["merchant_id", "is_mule"]], on="merchant_id", how="inner")
    merged = merged.merge(splits_df[["merchant_id", "split"]], on="merchant_id", how="inner")

    # Select only available behavioral features
    avail_behavioral_cols = [c for c in BEHAVIORAL_FEATURE_SUBSET if c in features_df.columns]

    train_mask = merged["split"] == "train"
    val_mask = merged["split"] == "val"
    test_mask = merged["split"] == "test"

    X_train = merged.loc[train_mask, avail_behavioral_cols].to_numpy()
    y_train = merged.loc[train_mask, "is_mule"].to_numpy()

    X_val = merged.loc[val_mask, avail_behavioral_cols].to_numpy()
    y_val = merged.loc[val_mask, "is_mule"].to_numpy()

    X_test = merged.loc[test_mask, avail_behavioral_cols].to_numpy()
    y_test = merged.loc[test_mask, "is_mule"].to_numpy()

    # 2. Train classifier
    model = create_classifier(seed=seed)
    model.fit(X_train, y_train)

    # 3. Optimize decision threshold on validation set
    val_probs = model.predict_proba(X_val)[:, 1]
    optimal_threshold = find_optimal_threshold(y_val, val_probs)

    # 4. Predict on full dataset
    all_X = merged[avail_behavioral_cols].to_numpy()
    all_probs = model.predict_proba(all_X)[:, 1]
    all_risk_scores = compute_risk_score(all_probs)
    all_preds = (all_probs >= optimal_threshold).astype(int)

    predictions_df = pd.DataFrame({
        "merchant_id": merged["merchant_id"],
        "split": merged["split"],
        "is_mule": merged["is_mule"],
        "mule_probability": np.round(all_probs, 4),
        "risk_score": all_risk_scores,
        "predicted_label": all_preds,
    })

    # 5. Evaluate on test set
    test_probs = model.predict_proba(X_test)[:, 1]
    test_metrics = evaluate_predictions(y_test, test_probs, threshold=optimal_threshold)
    test_metrics["model_name"] = "Baseline (Behavior Only)"
    test_metrics["feature_count"] = len(avail_behavioral_cols)

    return model, test_metrics, predictions_df, optimal_threshold


def main() -> None:
    """Train and evaluate the Baseline model."""
    parser = argparse.ArgumentParser(description="Train baseline behavior-only model.")
    parser.add_argument("--features-file", type=Path, default=Path("data/processed/merchant_features.csv"))
    parser.add_argument("--labels-file", type=Path, default=Path("data/processed/merchant_labels.csv"))
    parser.add_argument("--splits-file", type=Path, default=Path("data/processed/splits.csv"))
    parser.add_argument("--predictions-output", type=Path, default=Path("reports/baseline_predictions.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("Loading datasets for Baseline model training...")
    features_df = pd.read_csv(args.features_file)
    labels_df = pd.read_csv(args.labels_file)
    splits_df = pd.read_csv(args.splits_file)

    print("Training Baseline (Behavior-Only) model...")
    model, metrics, preds_df, threshold = train_baseline_model(
        features_df=features_df,
        labels_df=labels_df,
        splits_df=splits_df,
        seed=args.seed,
    )

    args.predictions_output.parent.mkdir(parents=True, exist_ok=True)
    preds_df.to_csv(args.predictions_output, index=False)

    print("\n--- Baseline Model Test Performance ---")
    print(f"Features Used: {metrics['feature_count']} (Behavioral Only)")
    print(f"Optimal Threshold: {metrics['threshold']}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"PR-AUC:    {metrics['pr_auc']:.4f}")
    print(f"FPR:       {metrics['false_positive_rate']:.4f}")
    print(f"Predictions saved to {args.predictions_output}")


if __name__ == "__main__":
    main()
