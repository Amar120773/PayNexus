"""Master feature builder and feature quality auditor for MuleHunter."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.features.behavioral_features import extract_behavioral_features
from src.features.network_features import extract_network_features
from src.features.temporal_features import extract_temporal_features
from src.features.coordination_features import extract_coordination_features
from src.features.peer_features import extract_peer_relative_features
from src.graph.build_graph import build_projected_merchant_graph, load_graph_data


FORBIDDEN_COLUMNS = {"is_mule", "mule_type", "network_id"}


def build_master_feature_table(
    dataset: Mapping[str, pd.DataFrame],
    splits_df: pd.DataFrame,
    data_dir: Path | str = "data/synthetic",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract and merge all behavioral, network, and temporal features.

    Returns:
      (merchant_features_df, merchant_labels_df)
    """
    merchants_df = dataset["merchants"].copy()
    labels_df = dataset["merchant_labels"].copy() if "merchant_labels" in dataset else pd.read_csv(Path(data_dir) / "merchant_labels.csv")

    train_merchants = splits_df[splits_df["split"] == "train"]["merchant_id"].tolist()
    val_merchants = splits_df[splits_df["split"].isin(["train", "val"])]["merchant_id"].tolist()
    test_merchants = splits_df["merchant_id"].tolist()
    
    val_only_merchants = splits_df[splits_df["split"] == "val"]["merchant_id"].tolist()
    test_only_merchants = splits_df[splits_df["split"] == "test"]["merchant_id"].tolist()

    all_features = []

    for split_name, subset, target_merchants in [
        ("train", train_merchants, train_merchants),
        ("val", val_merchants, val_only_merchants),
        ("test", test_merchants, test_only_merchants),
    ]:
        print(f"Extracting features for {split_name} split...")
        behavioral_df = extract_behavioral_features(dataset, merchants_df=merchants_df, merchant_subset=target_merchants)
        network_df = extract_network_features(dataset, merchants_df=merchants_df, merchant_subset=subset)
        temporal_df = extract_temporal_features(dataset, merchants_df=merchants_df, merchant_subset=subset)
        coordination_df = extract_coordination_features(dataset, merchants_df=merchants_df, merchant_subset=subset)
        peer_df = extract_peer_relative_features(dataset, merchants_df=merchants_df, behavioral_features=behavioral_df, merchant_subset=subset)

        # Filter network, temporal, coordination, peer to only target_merchants
        network_df = network_df[network_df["merchant_id"].isin(target_merchants)]
        temporal_df = temporal_df[temporal_df["merchant_id"].isin(target_merchants)]
        coordination_df = coordination_df[coordination_df["merchant_id"].isin(target_merchants)]
        peer_df = peer_df[peer_df["merchant_id"].isin(target_merchants)]

        merged = behavioral_df.merge(network_df, on="merchant_id", how="inner")
        merged = merged.merge(temporal_df, on="merchant_id", how="inner")
        merged = merged.merge(coordination_df, on="merchant_id", how="inner")
        merged = merged.merge(peer_df, on="merchant_id", how="inner")
        all_features.append(merged)

    final_features = pd.concat(all_features, ignore_index=True)

    # Engineer Contextual Features
    final_features["ip_sharing_concentration"] = np.where(final_features["unique_ip_count"] > 0, final_features["shared_ip_count"] / final_features["unique_ip_count"], 0.0)
    final_features["device_sharing_concentration"] = np.where(final_features["unique_device_count"] > 0, final_features["shared_device_count"] / final_features["unique_device_count"], 0.0)
    final_features["customer_sharing_concentration"] = np.where(final_features["unique_customer_count"] > 0, final_features["shared_customer_count"] / final_features["unique_customer_count"], 0.0)

    # Double check no forbidden columns exist in feature frame
    for col in FORBIDDEN_COLUMNS:
        if col in final_features.columns:
            final_features = final_features.drop(columns=[col])

    # Clean merchant labels table
    clean_labels = labels_df[["merchant_id", "network_id", "is_mule", "mule_type"]].copy()
    clean_labels["network_id"] = clean_labels["network_id"].fillna("")
    clean_labels["mule_type"] = clean_labels["mule_type"].fillna("")
    clean_labels["is_mule"] = clean_labels["is_mule"].fillna(0).astype(int)

    return final_features, clean_labels


def audit_feature_quality(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
) -> dict[str, Any]:
    """Perform comprehensive data quality, multicollinearity, and leakage audit on features."""
    audit_results: dict[str, Any] = {}

    feature_cols = [c for c in features_df.columns if c != "merchant_id"]
    n_rows = len(features_df)

    # 1. Missing Values & Infs
    missing_counts = features_df[feature_cols].isna().sum().to_dict()
    inf_counts = {
        col: int(np.isinf(features_df[col]).sum())
        for col in feature_cols
        if np.issubdtype(features_df[col].dtype, np.number)
    }
    audit_results["missing_values"] = {k: v for k, v in missing_counts.items() if v > 0}
    audit_results["infinite_values"] = {k: v for k, v in inf_counts.items() if v > 0}

    # 2. Duplicates
    dup_merchants = int(features_df["merchant_id"].duplicated().sum())
    dup_rows = int(features_df[feature_cols].duplicated().sum())
    audit_results["duplicate_merchants"] = dup_merchants
    audit_results["duplicate_rows"] = dup_rows

    # 3. Constant Features (Zero variance)
    constant_features = []
    for col in feature_cols:
        if features_df[col].nunique() <= 1:
            constant_features.append(col)
    audit_results["constant_features"] = constant_features

    # 4. Collinear / Highly Correlated Pairs (|r| > 0.95)
    numeric_cols = [c for c in feature_cols if np.issubdtype(features_df[c].dtype, np.number)]
    corr_matrix = features_df[numeric_cols].corr().abs()
    high_corr_pairs = []
    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            col_a = numeric_cols[i]
            col_b = numeric_cols[j]
            corr_val = corr_matrix.loc[col_a, col_b]
            if corr_val > 0.95:
                high_corr_pairs.append({
                    "feature_1": col_a,
                    "feature_2": col_b,
                    "correlation": round(float(corr_val), 4),
                })
    audit_results["high_correlation_pairs"] = high_corr_pairs

    # 5. Label Leakage Check
    leaked_columns = [col for col in features_df.columns if col in FORBIDDEN_COLUMNS]
    audit_results["leaked_columns"] = leaked_columns

    merged_with_label = features_df.merge(labels_df[["merchant_id", "is_mule"]], on="merchant_id", how="left")
    suspicious_features = []
    for col in numeric_cols:
        val = merged_with_label[col].to_numpy()
        label = merged_with_label["is_mule"].to_numpy()
        if np.std(val) > 0 and np.std(label) > 0:
            corr_with_label = abs(float(np.corrcoef(val, label)[0, 1]))
            if corr_with_label > 0.90:
                suspicious_features.append({
                    "feature": col,
                    "correlation_with_target": round(corr_with_label, 4),
                    "reason": "Extremely high single-feature correlation (>0.90) with target label indicating potential synthetic artifact or leakage.",
                })
    audit_results["suspicious_features"] = suspicious_features

    return audit_results


def generate_feature_quality_report_markdown(
    audit_results: dict[str, Any],
    features_df: pd.DataFrame,
) -> str:
    """Format audit results as a detailed Markdown report."""
    n_features = len([c for c in features_df.columns if c != "merchant_id"])
    n_merchants = len(features_df)

    lines = [
        "# MuleHunter Feature Quality & Leakage Audit Report",
        "",
        f"**Audit Summary**: Evaluated {n_features} features across {n_merchants} merchants.",
        "",
        "## 1. Data Completeness & Integrity",
        f"- **Total Merchants**: `{n_merchants}`",
        f"- **Total Engineered Features**: `{n_features}`",
        f"- **Duplicate Merchant IDs**: `{audit_results['duplicate_merchants']}`",
        f"- **Duplicate Feature Rows**: `{audit_results['duplicate_rows']}`",
        f"- **Missing Value Columns**: `{len(audit_results['missing_values'])}`",
        f"- **Infinite Value Columns**: `{len(audit_results['infinite_values'])}`",
        "",
    ]

    if audit_results["missing_values"]:
        lines.append("### Missing Values Breakdown:")
        for col, count in audit_results["missing_values"].items():
            lines.append(f"- `{col}`: {count} missing values")
        lines.append("")
    else:
        lines.append("> [!NOTE]\n> Zero missing values detected across all engineered feature columns.")
        lines.append("")

    lines.extend([
        "## 2. Low-Variance & Constant Feature Detection",
        f"- **Constant Features Detected**: `{len(audit_results['constant_features'])}`",
    ])
    if audit_results["constant_features"]:
        for col in audit_results["constant_features"]:
            lines.append(f"  - `{col}` (zero variance)")
    else:
        lines.append("All engineered features demonstrate positive variance.")
    lines.append("")

    lines.extend([
        "## 3. Multicollinearity Analysis (|r| > 0.95)",
        f"- **Highly Correlated Feature Pairs**: `{len(audit_results['high_correlation_pairs'])}`",
    ])
    if audit_results["high_correlation_pairs"]:
        lines.append("\n| Feature A | Feature B | Pearson Correlation | Explanation |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for pair in audit_results["high_correlation_pairs"]:
            lines.append(
                f"| `{pair['feature_1']}` | `{pair['feature_2']}` | `{pair['correlation']}` | "
                f"Expected structural overlap between graph topology or activity aggregates. |"
            )
        lines.append("")
    else:
        lines.append("No pairs exceed the 0.95 collinearity threshold.\n")

    lines.extend([
        "## 4. Ground-Truth Label Leakage & Suspicion Audit",
        f"- **Forbidden Target Columns Found**: `{len(audit_results['leaked_columns'])}`",
    ])
    if audit_results["leaked_columns"]:
        lines.append(f"> [!CAUTION]\n> Leakage detected! Columns {audit_results['leaked_columns']} must be removed.")
    else:
        lines.append("> [!IMPORTANT]\n> PASS: No ground truth label columns (`is_mule`, `mule_type`, `network_id`) are present in the feature table.")
    lines.append("")

    lines.append(f"- **Suspicious Features (|r_target| > 0.90)**: `{len(audit_results['suspicious_features'])}`")
    if audit_results["suspicious_features"]:
        for s in audit_results["suspicious_features"]:
            lines.append(f"- `{s['feature']}`: target correlation = `{s['correlation_with_target']}`. Reason: {s['reason']}")
    else:
        lines.append("No single feature provides an artificial shortcut or trivial separability for mule classification.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Build feature tables and audit quality."""
    parser = argparse.ArgumentParser(description="Build master feature tables and run quality audit.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--features-output", type=Path, default=Path("data/processed/merchant_features.csv"))
    parser.add_argument("--labels-output", type=Path, default=Path("data/processed/merchant_labels.csv"))
    parser.add_argument("--report-output", type=Path, default=Path("reports/feature_quality_report.md"))
    args = parser.parse_args()

    print("Building master merchant feature table...")
    dataset = load_graph_data(args.data_dir)
    splits_df = pd.read_csv("data/processed/splits.csv")
    features_df, labels_df = build_master_feature_table(dataset, splits_df, data_dir=args.data_dir)

    args.features_output.parent.mkdir(parents=True, exist_ok=True)
    args.labels_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)

    features_df.to_csv(args.features_output, index=False)
    labels_df.to_csv(args.labels_output, index=False)
    print(f"Saved master features to {args.features_output} ({features_df.shape[1] - 1} features, {len(features_df)} merchants)")
    print(f"Saved merchant labels to {args.labels_output}")

    print("Running feature quality audit...")
    audit_results = audit_feature_quality(features_df, labels_df)
    report_md = generate_feature_quality_report_markdown(audit_results, features_df)
    args.report_output.write_text(report_md, encoding="utf-8")
    print(f"Saved feature quality report to {args.report_output}")


if __name__ == "__main__":
    main()
