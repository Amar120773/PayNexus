"""End-to-end Day 3 execution pipeline for MuleHunter."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.evaluation.evaluate import (
    generate_evaluation_report_markdown,
    run_ablation_study,
)
from src.evaluation.network_split import generate_network_splits, save_splits
from src.features.build_features import (
    audit_feature_quality,
    build_master_feature_table,
    generate_feature_quality_report_markdown,
)
from src.graph.build_graph import (
    build_heterogeneous_graph,
    build_projected_merchant_graph,
    compute_graph_statistics,
    load_graph_data,
    save_graph_statistics,
)
from src.models.baseline import train_baseline_model
from src.models.mulehunter import train_mulehunter_model


def run_full_pipeline(
    data_dir: Path | str = "data/synthetic",
    processed_dir: Path | str = "data/processed",
    reports_dir: Path | str = "reports",
    seed: int = 42,
) -> None:
    """Execute all Day 3 pipeline stages end-to-end."""
    data_path = Path(data_dir)
    proc_path = Path(processed_dir)
    rep_path = Path(reports_dir)

    proc_path.mkdir(parents=True, exist_ok=True)
    rep_path.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("STEP 1: Graph Construction & Statistics")
    print("==================================================")
    dataset = load_graph_data(data_path)
    hetero_graph = build_heterogeneous_graph(dataset)
    projected_graph = build_projected_merchant_graph(dataset)
    graph_stats = compute_graph_statistics(hetero_graph, projected_graph)
    save_graph_statistics(graph_stats, rep_path / "graph_statistics.json")
    print(f"Graph stats saved to {rep_path / 'graph_statistics.json'}")

    print("\n==================================================")
    print("STEP 2: Network-Level Train/Val/Test Split")
    print("==================================================")
    labels_df = pd.read_csv(data_path / "merchant_labels.csv")
    merchants_df = pd.read_csv(data_path / "merchants.csv")
    splits_df = generate_network_splits(
        labels_df=labels_df,
        merchants_df=merchants_df,
        projected_graph=projected_graph,
        seed=seed,
    )
    save_splits(splits_df, proc_path / "splits.csv")
    print(f"Splits saved to {proc_path / 'splits.csv'}")

    print("\n==================================================")
    print("STEP 3: Master Feature Engineering & Quality Audit")
    print("==================================================")
    features_df, clean_labels = build_master_feature_table(dataset, splits_df, data_dir=data_path)
    features_df.to_csv(proc_path / "merchant_features.csv", index=False)
    clean_labels.to_csv(proc_path / "merchant_labels.csv", index=False)
    print(f"Merchant features saved to {proc_path / 'merchant_features.csv'}")
    print(f"Merchant labels saved to {proc_path / 'merchant_labels.csv'}")

    audit_results = audit_feature_quality(features_df, clean_labels)
    quality_md = generate_feature_quality_report_markdown(audit_results, features_df)
    (rep_path / "feature_quality_report.md").write_text(quality_md, encoding="utf-8")
    print(f"Feature quality report saved to {rep_path / 'feature_quality_report.md'}")

    print("\n==================================================")
    print("STEP 4: Baseline Model Training (Behavior Only)")
    print("==================================================")
    base_model, base_metrics, base_preds, base_thresh = train_baseline_model(
        features_df=features_df,
        labels_df=clean_labels,
        splits_df=splits_df,
        seed=seed,
    )
    base_preds.to_csv(rep_path / "baseline_predictions.csv", index=False)
    print(f"Baseline F1: {base_metrics['f1']:.4f}, ROC-AUC: {base_metrics['roc_auc']:.4f}, PR-AUC: {base_metrics['pr_auc']:.4f}")

    print("\n==================================================")
    print("STEP 5: Full MuleHunter Model Training")
    print("==================================================")
    mule_model, mule_metrics, mule_preds, mule_thresh, mule_imp = train_mulehunter_model(
        features_df=features_df,
        labels_df=clean_labels,
        splits_df=splits_df,
        seed=seed,
    )
    mule_preds.to_csv(rep_path / "mulehunter_predictions.csv", index=False)
    mule_imp.to_csv(rep_path / "feature_importance.csv", index=False)
    print(f"MuleHunter F1: {mule_metrics['f1']:.4f}, ROC-AUC: {mule_metrics['roc_auc']:.4f}, PR-AUC: {mule_metrics['pr_auc']:.4f}")

    print("\n==================================================")
    print("STEP 6: Ablation Study & Evaluation Report")
    print("==================================================")
    comparison_df, artifacts = run_ablation_study(
        features_df=features_df,
        labels_df=clean_labels,
        splits_df=splits_df,
        seed=seed,
    )
    comparison_df.to_csv(rep_path / "model_comparison.csv", index=False)
    eval_md = generate_evaluation_report_markdown(
        comparison_df=comparison_df,
        trained_artifacts=artifacts,
        splits_df=splits_df,
        labels_df=clean_labels,
    )
    (rep_path / "evaluation_report.md").write_text(eval_md, encoding="utf-8")
    print(f"Ablation comparison saved to {rep_path / 'model_comparison.csv'}")
    print(f"Evaluation report saved to {rep_path / 'evaluation_report.md'}")
    print("\nAll Day 3 deliverables generated successfully!")


if __name__ == "__main__":
    run_full_pipeline()
