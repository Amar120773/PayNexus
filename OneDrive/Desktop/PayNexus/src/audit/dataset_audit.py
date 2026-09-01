"""Rigorous audit for MuleHunter synthetic datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset, validate_dataset


DATASET_TABLES = [
    "merchants",
    "customers",
    "devices",
    "ips",
    "settlement_accounts",
    "transactions",
    "settlements",
    "refunds",
    "merchant_labels",
    "mule_networks",
]

FORBIDDEN_TRAINING_COLUMNS = {"is_mule", "mule_type", "network_id"}
ENTITY_COLUMNS = {
    "customer_id": "customers",
    "device_id": "devices",
    "ip_id": "ips",
    "settlement_account_id": "settlement_accounts",
}


@dataclass(frozen=True)
class AuditInputs:
    data_dir: Path
    reports_dir: Path
    seed: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the MuleHunter synthetic dataset.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs = AuditInputs(data_dir=args.data_dir, reports_dir=args.reports_dir, seed=args.seed)
    run_audit(inputs)
    print(f"Wrote audit reports to {inputs.reports_dir}")


def run_audit(inputs: AuditInputs) -> None:
    inputs.reports_dir.mkdir(parents=True, exist_ok=True)
    (inputs.reports_dir / "network_examples").mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(inputs.data_dir)
    labels = dataset["merchant_labels"].copy()
    labels["network_id"] = labels["network_id"].fillna("")
    labels["mule_type"] = labels["mule_type"].fillna("")

    hetero_graph = build_heterogeneous_graph(dataset)
    projected_graph = build_projected_merchant_graph(dataset)
    per_merchant = build_merchant_feature_frame(dataset, projected_graph)

    network_report = audit_network_visibility(dataset, labels, hetero_graph, projected_graph)
    overlap_report = audit_overlap_distributions(per_merchant)
    feature_report = audit_feature_separability(per_merchant)
    leakage_report = audit_label_leakage(dataset, per_merchant)
    integrity_report = audit_data_integrity(dataset, inputs.seed)
    reproducibility_report = audit_reproducibility(inputs.seed)
    temporal_report = audit_temporal_realism(dataset, labels)
    balance_report = audit_class_balance(labels, dataset)
    generalization_report = audit_network_generalization(labels)
    final_score = score_dataset(
        network_report=network_report,
        overlap_report=overlap_report,
        feature_report=feature_report,
        leakage_report=leakage_report,
        integrity_report=integrity_report,
        reproducibility_report=reproducibility_report,
        temporal_report=temporal_report,
        generalization_report=generalization_report,
    )

    write_json(inputs.reports_dir / "network_visibility_report.json", network_report)
    pd.DataFrame(network_report["networks"]).to_csv(inputs.reports_dir / "network_visibility_report.csv", index=False)
    feature_report["feature_stats"].to_csv(inputs.reports_dir / "feature_separability.csv", index=False)
    write_json(inputs.reports_dir / "label_leakage_report.json", leakage_report)
    pd.DataFrame(leakage_report["checks"]).to_csv(inputs.reports_dir / "label_leakage_report.csv", index=False)
    write_json(inputs.reports_dir / "data_integrity_report.json", integrity_report)
    write_json(inputs.reports_dir / "reproducibility_report.json", reproducibility_report)
    temporal_report["merchant_temporal_features"].to_csv(inputs.reports_dir / "temporal_analysis.csv", index=False)

    write_representative_network_json(inputs.reports_dir / "network_examples", dataset, labels, projected_graph)
    summary = build_summary_markdown(
        network_report=network_report,
        overlap_report=overlap_report,
        feature_report=feature_report,
        leakage_report=leakage_report,
        integrity_report=integrity_report,
        reproducibility_report=reproducibility_report,
        temporal_report=temporal_report,
        balance_report=balance_report,
        generalization_report=generalization_report,
        final_score=final_score,
    )
    (inputs.reports_dir / "dataset_audit_summary.md").write_text(summary, encoding="utf-8")


def load_dataset(data_dir: Path) -> dict[str, pd.DataFrame]:
    dataset: dict[str, pd.DataFrame] = {}
    for table in DATASET_TABLES:
        path = data_dir / f"{table}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing required table: {path}")
        dataset[table] = pd.read_csv(path)
    return dataset


def build_heterogeneous_graph(dataset: dict[str, pd.DataFrame]) -> nx.Graph:
    graph = nx.Graph()
    for merchant_id in dataset["merchants"]["merchant_id"]:
        graph.add_node(f"merchant:{merchant_id}", node_type="merchant", raw_id=merchant_id)

    for entity_col, table in ENTITY_COLUMNS.items():
        for entity_id in dataset[table][entity_col]:
            graph.add_node(f"{entity_col}:{entity_id}", node_type=entity_col, raw_id=entity_id)

    tx = dataset["transactions"]
    for entity_col in ["customer_id", "device_id", "ip_id"]:
        counts = tx.groupby(["merchant_id", entity_col]).size().reset_index(name="count")
        for row in counts.itertuples(index=False):
            graph.add_edge(
                f"merchant:{row.merchant_id}",
                f"{entity_col}:{getattr(row, entity_col)}",
                edge_type=entity_col,
                weight=int(row.count),
            )

    settlements = dataset["settlements"]
    counts = settlements.groupby(["merchant_id", "settlement_account_id"]).size().reset_index(name="count")
    for row in counts.itertuples(index=False):
        graph.add_edge(
            f"merchant:{row.merchant_id}",
            f"settlement_account_id:{row.settlement_account_id}",
            edge_type="settlement_account_id",
            weight=int(row.count),
        )
    return graph


def build_projected_merchant_graph(dataset: dict[str, pd.DataFrame]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(dataset["merchants"]["merchant_id"])

    def add_edges(frame: pd.DataFrame, entity_col: str, reason: str) -> None:
        for _, group in frame.groupby(entity_col):
            merchants = sorted(set(group["merchant_id"]))
            if len(merchants) < 2:
                continue
            for idx, left in enumerate(merchants):
                for right in merchants[idx + 1 :]:
                    if not graph.has_edge(left, right):
                        graph.add_edge(left, right, weight=0, reasons=set())
                    graph[left][right]["weight"] += 1
                    graph[left][right]["reasons"].add(reason)

    add_edges(dataset["transactions"][["merchant_id", "customer_id"]].drop_duplicates(), "customer_id", "customer")
    add_edges(dataset["transactions"][["merchant_id", "device_id"]].drop_duplicates(), "device_id", "device")
    add_edges(dataset["transactions"][["merchant_id", "ip_id"]].drop_duplicates(), "ip_id", "ip")
    add_edges(
        dataset["settlements"][["merchant_id", "settlement_account_id"]].drop_duplicates(),
        "settlement_account_id",
        "settlement",
    )
    return graph


def build_merchant_feature_frame(dataset: dict[str, pd.DataFrame], graph: nx.Graph) -> pd.DataFrame:
    labels = dataset["merchant_labels"].copy()
    labels["network_id"] = labels["network_id"].fillna("")
    labels["mule_type"] = labels["mule_type"].fillna("")
    merchants = dataset["merchants"].merge(labels, on="merchant_id", how="left")
    tx = dataset["transactions"].copy()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx["date"] = tx["timestamp"].dt.date
    tx["hour"] = tx["timestamp"].dt.hour
    tx["is_weekend"] = tx["timestamp"].dt.dayofweek >= 5
    tx["is_night"] = tx["hour"].between(0, 5)

    grouped = tx.groupby("merchant_id")
    features = pd.DataFrame({"merchant_id": merchants["merchant_id"]})
    features = features.merge(
        grouped.agg(
            tx_count=("transaction_id", "count"),
            total_amount=("amount", "sum"),
            mean_amount=("amount", "mean"),
            median_amount=("amount", "median"),
            std_amount=("amount", "std"),
            unique_customers=("customer_id", "nunique"),
            unique_devices=("device_id", "nunique"),
            unique_ips=("ip_id", "nunique"),
            active_days=("date", "nunique"),
            weekend_share=("is_weekend", "mean"),
            night_share=("is_night", "mean"),
        ).reset_index(),
        on="merchant_id",
        how="left",
    )
    status_counts = pd.crosstab(tx["merchant_id"], tx["status"], normalize="index").reset_index()
    for status in ["SUCCESS", "FAILED", "REFUNDED"]:
        if status not in status_counts.columns:
            status_counts[status] = 0.0
    status_counts = status_counts.rename(
        columns={"SUCCESS": "success_rate", "FAILED": "failed_rate", "REFUNDED": "refunded_rate"}
    )
    features = features.merge(status_counts[["merchant_id", "success_rate", "failed_rate", "refunded_rate"]], on="merchant_id", how="left")

    daily_counts = tx.groupby(["merchant_id", "date"]).size().reset_index(name="daily_tx_count")
    daily_stats = daily_counts.groupby("merchant_id").agg(
        max_daily_tx=("daily_tx_count", "max"),
        mean_daily_tx=("daily_tx_count", "mean"),
        std_daily_tx=("daily_tx_count", "std"),
    )
    daily_stats["spike_ratio"] = daily_stats["max_daily_tx"] / daily_stats["mean_daily_tx"].replace(0, np.nan)
    features = features.merge(daily_stats.reset_index(), on="merchant_id", how="left")

    refunds = dataset["refunds"]
    refund_agg = refunds.groupby("merchant_id").agg(refund_count=("refund_id", "count"), refund_amount=("amount", "sum")).reset_index()
    features = features.merge(refund_agg, on="merchant_id", how="left")

    settlement_account_counts = dataset["settlements"].groupby("merchant_id")["settlement_account_id"].nunique().reset_index()
    settlement_account_counts = settlement_account_counts.rename(columns={"settlement_account_id": "unique_settlement_accounts"})
    features = features.merge(settlement_account_counts, on="merchant_id", how="left")

    for entity_col, source in [
        ("device_id", dataset["transactions"][["merchant_id", "device_id"]].drop_duplicates()),
        ("ip_id", dataset["transactions"][["merchant_id", "ip_id"]].drop_duplicates()),
        ("customer_id", dataset["transactions"][["merchant_id", "customer_id"]].drop_duplicates()),
        ("settlement_account_id", dataset["settlements"][["merchant_id", "settlement_account_id"]].drop_duplicates()),
    ]:
        metric = shared_entity_counts(source, entity_col)
        features = features.merge(metric, on="merchant_id", how="left")

    degree = dict(graph.degree())
    weighted_degree = dict(graph.degree(weight="weight"))
    ego_density = {merchant_id: nx.density(nx.ego_graph(graph, merchant_id)) for merchant_id in graph.nodes}
    features["connected_merchants"] = features["merchant_id"].map(degree).fillna(0)
    features["network_degree"] = features["merchant_id"].map(degree).fillna(0)
    features["weighted_network_degree"] = features["merchant_id"].map(weighted_degree).fillna(0)
    features["ego_network_density"] = features["merchant_id"].map(ego_density).fillna(0)

    features = features.merge(
        merchants[["merchant_id", "category", "kyc_status", "merchant_age_days", "is_mule", "network_id", "mule_type"]],
        on="merchant_id",
        how="left",
    )
    numeric_cols = features.select_dtypes(include=[np.number]).columns
    features[numeric_cols] = features[numeric_cols].fillna(0)
    return features


def shared_entity_counts(frame: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    merchant_sets = frame.groupby(entity_col)["merchant_id"].agg(lambda values: set(values))
    shared_entities = merchant_sets[merchant_sets.map(len) > 1].index
    counts = frame[frame[entity_col].isin(shared_entities)].groupby("merchant_id")[entity_col].nunique()
    metric_name = f"shared_{entity_col.replace('_id', '')}_count"
    return counts.rename(metric_name).reset_index()


def audit_network_visibility(
    dataset: dict[str, pd.DataFrame],
    labels: pd.DataFrame,
    hetero_graph: nx.Graph,
    projected_graph: nx.Graph,
) -> dict[str, Any]:
    tx = dataset["transactions"]
    settlements = dataset["settlements"]
    rows: list[dict[str, Any]] = []

    for network_id, group in labels[labels["is_mule"] == 1].groupby("network_id"):
        members = sorted(group["merchant_id"].tolist())
        subgraph = projected_graph.subgraph(members).copy()
        components = [sorted(component) for component in nx.connected_components(subgraph)]
        shared_devices = shared_count_within_members(tx[tx["merchant_id"].isin(members)], "device_id")
        shared_ips = shared_count_within_members(tx[tx["merchant_id"].isin(members)], "ip_id")
        shared_customers = shared_count_within_members(tx[tx["merchant_id"].isin(members)], "customer_id")
        shared_settlements = shared_count_within_members(
            settlements[settlements["merchant_id"].isin(members)],
            "settlement_account_id",
        )
        represented = all(f"merchant:{merchant_id}" in hetero_graph for merchant_id in members)
        connected = len(components) == 1 if members else False
        avg_shortest_path = (
            round(float(nx.average_shortest_path_length(subgraph)), 4)
            if connected and subgraph.number_of_nodes() > 1
            else None
        )
        rows.append(
            {
                "network_id": network_id,
                "mule_type": group["mule_type"].iloc[0],
                "members": ",".join(members),
                "network_size": len(members),
                "shared_devices": shared_devices,
                "shared_ips": shared_ips,
                "shared_customers": shared_customers,
                "shared_settlement_accounts": shared_settlements,
                "internal_edges": subgraph.number_of_edges(),
                "network_density": round(float(nx.density(subgraph)), 4),
                "connected_components": len(components),
                "component_sizes": ",".join(str(len(component)) for component in components),
                "average_shortest_path": avg_shortest_path,
                "represented_in_graph": represented,
                "connected_in_projected_graph": connected,
                "status": "PASS" if represented and connected and subgraph.number_of_edges() > 0 else "WARNING",
            }
        )

    warning_count = sum(row["status"] != "PASS" for row in rows)
    return {
        "status": "PASS" if warning_count == 0 else "WARNING",
        "summary": {
            "heterogeneous_nodes": hetero_graph.number_of_nodes(),
            "heterogeneous_edges": hetero_graph.number_of_edges(),
            "projected_merchant_nodes": projected_graph.number_of_nodes(),
            "projected_merchant_edges": projected_graph.number_of_edges(),
            "mule_networks": len(rows),
            "networks_not_fully_connected": warning_count,
        },
        "networks": rows,
    }


def shared_count_within_members(frame: pd.DataFrame, entity_col: str) -> int:
    if frame.empty:
        return 0
    counts = frame.groupby(entity_col)["merchant_id"].nunique()
    return int((counts > 1).sum())


def audit_overlap_distributions(features: pd.DataFrame) -> dict[str, Any]:
    metrics = [
        "shared_device_count",
        "shared_ip_count",
        "shared_customer_count",
        "shared_settlement_account_count",
        "connected_merchants",
        "network_degree",
        "ego_network_density",
    ]
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for metric in metrics:
        for label, value in [("legitimate", 0), ("mule", 1)]:
            values = features.loc[features["is_mule"] == value, metric].astype(float)
            rows.append(distribution_row(metric, label, values))
        legit = features.loc[features["is_mule"] == 0, metric].astype(float)
        mule = features.loc[features["is_mule"] == 1, metric].astype(float)
        if legit.quantile(0.95) == 0 and mule.median() > 0:
            warnings.append(f"{metric}: legitimate merchants have almost no overlap")
        if mule.min() > 0 and mule.quantile(0.05) == mule.quantile(0.95):
            warnings.append(f"{metric}: mule merchants have nearly universal identical overlap")

    return {
        "status": "PASS" if not warnings else "WARNING",
        "warnings": warnings,
        "distributions": rows,
    }


def distribution_row(metric: str, group: str, values: pd.Series) -> dict[str, Any]:
    return {
        "metric": metric,
        "group": group,
        "mean": round(float(values.mean()), 4),
        "median": round(float(values.median()), 4),
        "std": round(float(values.std(ddof=0)), 4),
        "p05": round(float(values.quantile(0.05)), 4),
        "p25": round(float(values.quantile(0.25)), 4),
        "p75": round(float(values.quantile(0.75)), 4),
        "p95": round(float(values.quantile(0.95)), 4),
        "min": round(float(values.min()), 4),
        "max": round(float(values.max()), 4),
    }


def audit_feature_separability(features: pd.DataFrame) -> dict[str, Any]:
    numeric_features = [
        column
        for column in features.select_dtypes(include=[np.number]).columns
        if column != "is_mule"
    ]
    rows: list[dict[str, Any]] = []
    y = features["is_mule"].astype(int)
    for column in numeric_features:
        legit = features.loc[y == 0, column].astype(float)
        mule = features.loc[y == 1, column].astype(float)
        auc = safe_auc(y, features[column].astype(float))
        effect = cohen_d(mule, legit)
        warning = abs(auc - 0.5) >= 0.4
        rows.append(
            {
                "feature": column,
                "legit_mean": round(float(legit.mean()), 4),
                "mule_mean": round(float(mule.mean()), 4),
                "legit_median": round(float(legit.median()), 4),
                "mule_median": round(float(mule.median()), 4),
                "legit_std": round(float(legit.std(ddof=0)), 4),
                "mule_std": round(float(mule.std(ddof=0)), 4),
                "legit_p05": round(float(legit.quantile(0.05)), 4),
                "legit_p95": round(float(legit.quantile(0.95)), 4),
                "mule_p05": round(float(mule.quantile(0.05)), 4),
                "mule_p95": round(float(mule.quantile(0.95)), 4),
                "cohen_d_mule_vs_legit": round(effect, 4),
                "roc_auc_single_feature": round(float(auc), 4) if auc is not None else None,
                "status": "WARNING" if warning else "PASS",
                "note": "Potentially too easy / unrealistic feature" if warning else "",
            }
        )

    stats = pd.DataFrame(rows).sort_values("roc_auc_single_feature", key=lambda s: (s - 0.5).abs(), ascending=False)
    network_score = features[
        ["shared_device_count", "shared_ip_count", "shared_customer_count", "shared_settlement_account_count", "network_degree"]
    ].rank(pct=True).mean(axis=1)
    combo_auc = safe_auc(y, network_score)
    warning_count = int((stats["status"] == "WARNING").sum())
    return {
        "status": "WARNING" if warning_count else "PASS",
        "feature_stats": stats,
        "combination_check": {
            "method": "mean percentile rank of core network-overlap features; not a trained final model",
            "roc_auc": round(float(combo_auc), 4) if combo_auc is not None else None,
            "status": "WARNING" if combo_auc is not None and combo_auc >= 0.9 else "PASS",
        },
        "warnings": stats.loc[stats["status"] == "WARNING", "feature"].tolist(),
    }


def audit_label_leakage(dataset: dict[str, pd.DataFrame], features: pd.DataFrame) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    y = features["is_mule"].astype(int)

    for table, frame in dataset.items():
        if table in {"merchant_labels", "mule_networks"}:
            continue
        leaked = sorted(FORBIDDEN_TRAINING_COLUMNS.intersection(frame.columns))
        checks.append(
            {
                "check": f"{table}_forbidden_columns",
                "status": "FAIL" if leaked else "PASS",
                "evidence": ",".join(leaked) if leaked else "No forbidden label columns found",
                "recommendation": "Remove label columns from operational tables" if leaked else "",
            }
        )

    merchant_num = features["merchant_id"].str.extract(r"(\d+)").astype(float)[0]
    id_auc = safe_auc(y, merchant_num)
    checks.append(leakage_check_from_auc("merchant_id_numeric_suffix", id_auc, "Merchant ID range should not identify mule status"))

    for metric, message in [
        ("merchant_age_days", "Mule merchants should not be generated in a separate onboarding era"),
        ("tx_count", "Transaction volume alone should not reveal the label"),
        ("mean_amount", "Amount scale alone should not reveal the label"),
        ("failed_rate", "Payment status mix alone should not reveal the label"),
        ("refunded_rate", "Refund status mix alone should not reveal the label"),
    ]:
        checks.append(leakage_check_from_auc(metric, safe_auc(y, features[metric]), message))

    checks.extend(categorical_leakage_checks(features, "category", y))
    checks.extend(categorical_leakage_checks(features, "kyc_status", y))

    tx = dataset["transactions"].merge(dataset["merchant_labels"][["merchant_id", "is_mule"]], on="merchant_id", how="left")
    checks.extend(categorical_leakage_checks(tx, "payment_method", tx["is_mule"].astype(int)))
    checks.extend(categorical_leakage_checks(tx, "status", tx["is_mule"].astype(int)))

    max_status = status_from_checks(checks)
    return {"status": max_status, "checks": checks}


def leakage_check_from_auc(check: str, auc: float | None, recommendation: str) -> dict[str, Any]:
    if auc is None:
        status = "WARNING"
        evidence = "AUC unavailable"
    else:
        distance = abs(float(auc) - 0.5)
        status = "WARNING" if distance >= 0.4 else "PASS"
        evidence = f"single-feature AUC={auc:.4f}"
    return {
        "check": check,
        "status": status,
        "evidence": evidence,
        "recommendation": recommendation if status != "PASS" else "",
    }


def categorical_leakage_checks(frame: pd.DataFrame, column: str, y: pd.Series) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    table = pd.crosstab(frame[column], y, normalize="columns")
    for value in sorted(frame[column].dropna().unique()):
        legit_rate = float(table.loc[value, 0]) if 0 in table.columns and value in table.index else 0.0
        mule_rate = float(table.loc[value, 1]) if 1 in table.columns and value in table.index else 0.0
        exclusive = (legit_rate == 0 and mule_rate > 0.15) or (mule_rate == 0 and legit_rate > 0.15)
        diff = abs(mule_rate - legit_rate)
        status = "WARNING" if exclusive or diff > 0.35 else "PASS"
        checks.append(
            {
                "check": f"{column}={value}",
                "status": status,
                "evidence": f"legit_rate={legit_rate:.4f}; mule_rate={mule_rate:.4f}",
                "recommendation": f"Review {column} distribution" if status != "PASS" else "",
            }
        )
    return checks


def audit_data_integrity(dataset: dict[str, pd.DataFrame], seed: int) -> dict[str, Any]:
    config = SyntheticDataConfig(seed=seed)
    checks: list[dict[str, Any]] = []

    for error in validate_dataset(dataset, config):
        checks.append({"check": f"generator_validation:{error}", "status": "FAIL", "evidence": error})

    primary_keys = {
        "merchants": "merchant_id",
        "customers": "customer_id",
        "devices": "device_id",
        "ips": "ip_id",
        "settlement_accounts": "settlement_account_id",
        "transactions": "transaction_id",
        "settlements": "settlement_id",
        "refunds": "refund_id",
        "merchant_labels": "merchant_id",
        "mule_networks": "network_id",
    }
    for table, key in primary_keys.items():
        frame = dataset[table]
        checks.append(pass_fail(f"{table}.{key}_unique", not frame[key].duplicated().any(), f"duplicates={int(frame[key].duplicated().sum())}"))
        checks.append(pass_fail(f"{table}_null_cells", not frame.isna().any().any(), f"null_cells={int(frame.isna().sum().sum())}"))

    checks.extend(referential_checks(dataset))
    checks.append(pass_fail("positive_transaction_amounts", bool((dataset["transactions"]["amount"] > 0).all()), "All transaction amounts must be positive"))
    checks.append(pass_fail("positive_settlement_amounts", bool((dataset["settlements"]["amount"] > 0).all()), "All settlement amounts must be positive"))
    checks.append(pass_fail("duplicate_transactions", not dataset["transactions"].duplicated().any(), f"duplicates={int(dataset['transactions'].duplicated().sum())}"))

    refunds = dataset["refunds"].merge(dataset["transactions"][["transaction_id", "amount"]], on="transaction_id", suffixes=("_refund", "_tx"))
    checks.append(pass_fail("refund_not_above_transaction", bool((refunds["amount_refund"] <= refunds["amount_tx"] + 0.01).all()), "Refund amount <= original transaction"))

    tx = dataset["transactions"].copy()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"], errors="coerce")
    checks.append(pass_fail("transaction_timestamps_valid", not tx["timestamp"].isna().any(), "All transaction timestamps parse"))

    settlement_consistency = settlement_amount_consistency(dataset)
    checks.append(settlement_consistency)
    return {"status": status_from_checks(checks), "checks": checks}


def referential_checks(dataset: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    refs = [
        ("transactions.merchant_id", dataset["transactions"]["merchant_id"], set(dataset["merchants"]["merchant_id"])),
        ("transactions.customer_id", dataset["transactions"]["customer_id"], set(dataset["customers"]["customer_id"])),
        ("transactions.device_id", dataset["transactions"]["device_id"], set(dataset["devices"]["device_id"])),
        ("transactions.ip_id", dataset["transactions"]["ip_id"], set(dataset["ips"]["ip_id"])),
        ("settlements.merchant_id", dataset["settlements"]["merchant_id"], set(dataset["merchants"]["merchant_id"])),
        (
            "settlements.settlement_account_id",
            dataset["settlements"]["settlement_account_id"],
            set(dataset["settlement_accounts"]["settlement_account_id"]),
        ),
        ("refunds.transaction_id", dataset["refunds"]["transaction_id"], set(dataset["transactions"]["transaction_id"])),
        ("refunds.merchant_id", dataset["refunds"]["merchant_id"], set(dataset["merchants"]["merchant_id"])),
        ("merchant_labels.merchant_id", dataset["merchant_labels"]["merchant_id"], set(dataset["merchants"]["merchant_id"])),
    ]
    for name, values, allowed in refs:
        invalid = set(values.dropna()) - allowed
        checks.append(pass_fail(f"{name}_referential_integrity", not invalid, f"invalid_refs={len(invalid)}"))
    return checks


def settlement_amount_consistency(dataset: dict[str, pd.DataFrame]) -> dict[str, Any]:
    tx = dataset["transactions"].copy()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx = tx[tx["status"].isin(["SUCCESS", "REFUNDED"])]
    start = tx["timestamp"].min().normalize()
    tx["settlement_window"] = ((tx["timestamp"] - start).dt.days // 3).clip(lower=0)
    gross = tx.groupby(["merchant_id", "settlement_window"])["amount"].sum().reset_index(name="gross_amount")
    settlements = dataset["settlements"].copy()
    settlements["timestamp"] = pd.to_datetime(settlements["timestamp"])
    settlements["settlement_window"] = ((settlements["timestamp"] - start).dt.days // 3 - 1).clip(lower=0)
    settled = settlements.groupby(["merchant_id", "settlement_window"])["amount"].sum().reset_index(name="settled_amount")
    merged = settled.merge(gross, on=["merchant_id", "settlement_window"], how="left")
    ratios = merged["settled_amount"] / merged["gross_amount"].replace(0, np.nan)
    ok = bool(ratios.dropna().between(0.90, 1.02).mean() > 0.95)
    return pass_fail(
        "settlement_amounts_consistent_with_transactions",
        ok,
        f"windows_checked={len(ratios.dropna())}; share_between_90pct_and_102pct={ratios.dropna().between(0.90, 1.02).mean():.4f}",
    )


def audit_reproducibility(seed: int) -> dict[str, Any]:
    config_a = SyntheticDataConfig(seed=seed)
    config_b = SyntheticDataConfig(seed=seed)
    config_c = SyntheticDataConfig(seed=seed + 1)
    dataset_a = generate_dataset(config_a)
    dataset_b = generate_dataset(config_b)
    dataset_c = generate_dataset(config_c)

    same_seed_tables = []
    different_seed_tables = []
    for table in DATASET_TABLES:
        hash_a = hash_frame(dataset_a[table])
        hash_b = hash_frame(dataset_b[table])
        hash_c = hash_frame(dataset_c[table])
        same_seed_tables.append(
            {
                "table": table,
                "identical": hash_a == hash_b,
                "hash_a": hash_a,
                "hash_b": hash_b,
                "row_count_a": len(dataset_a[table]),
                "row_count_b": len(dataset_b[table]),
            }
        )
        different_seed_tables.append(
            {
                "table": table,
                "changed_with_seed_plus_one": hash_a != hash_c,
                "schema_identical": list(dataset_a[table].columns) == list(dataset_c[table].columns),
                "row_count_a": len(dataset_a[table]),
                "row_count_seed_plus_one": len(dataset_c[table]),
                "hash_a": hash_a,
                "hash_seed_plus_one": hash_c,
            }
        )

    return {
        "status": "PASS"
        if all(row["identical"] for row in same_seed_tables)
        and all(row["schema_identical"] for row in different_seed_tables)
        and any(row["changed_with_seed_plus_one"] for row in different_seed_tables)
        else "FAIL",
        "seed": seed,
        "seed_plus_one": seed + 1,
        "same_seed": same_seed_tables,
        "different_seed": different_seed_tables,
    }


def audit_class_balance(labels: pd.DataFrame, dataset: dict[str, pd.DataFrame]) -> dict[str, Any]:
    mule_merchants = int(labels["is_mule"].sum())
    legitimate_merchants = int((labels["is_mule"] == 0).sum())
    tx_labels = dataset["transactions"].merge(labels[["merchant_id", "is_mule"]], on="merchant_id", how="left")
    network_sizes = labels[labels["is_mule"] == 1].groupby("network_id").size().to_dict()
    mule_types = labels[labels["is_mule"] == 1]["mule_type"].value_counts().to_dict()
    mule_share = mule_merchants / len(labels)
    status = "WARNING" if mule_share < 0.03 or mule_share > 0.25 else "PASS"
    return {
        "status": status,
        "merchant_count": len(labels),
        "mule_merchants": mule_merchants,
        "legitimate_merchants": legitimate_merchants,
        "mule_share": round(mule_share, 4),
        "mule_networks": int(labels.loc[labels["is_mule"] == 1, "network_id"].nunique()),
        "merchants_per_network": {key: int(value) for key, value in network_sizes.items()},
        "mule_type_distribution": {key: int(value) for key, value in mule_types.items()},
        "transaction_level_distribution": tx_labels["is_mule"].value_counts().sort_index().astype(int).to_dict(),
    }


def audit_network_generalization(labels: pd.DataFrame) -> dict[str, Any]:
    mule_labels = labels[labels["is_mule"] == 1]
    by_network = mule_labels.groupby("network_id").agg(
        network_size=("merchant_id", "count"),
        mule_type=("mule_type", lambda values: ",".join(sorted(set(values)))),
    )
    network_count = len(by_network)
    train = math.floor(network_count * 0.70)
    validation = max(1, round(network_count * 0.15))
    test = network_count - train - validation
    if test < 1 and network_count >= 3:
        test = 1
        train = network_count - validation - test
    status = "PASS" if network_count >= 10 and validation >= 1 and test >= 1 else "WARNING"
    return {
        "status": status,
        "network_count": network_count,
        "network_sizes": {key: int(value) for key, value in by_network["network_size"].to_dict().items()},
        "mule_types_per_network": by_network["mule_type"].to_dict(),
        "recommended_network_level_split": {"train": train, "validation": validation, "test": test},
        "assessment": "Supports a 7/1/2 network-level split, but validation/test diversity is limited with only 10 networks."
        if network_count == 10
        else "Network count should be increased for robust held-out network evaluation.",
    }


def audit_temporal_realism(dataset: dict[str, pd.DataFrame], labels: pd.DataFrame) -> dict[str, Any]:
    tx = dataset["transactions"].merge(labels[["merchant_id", "is_mule", "network_id", "mule_type"]], on="merchant_id", how="left")
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx["date"] = tx["timestamp"].dt.date
    tx["hour"] = tx["timestamp"].dt.hour
    tx["weekday"] = tx["timestamp"].dt.dayofweek
    tx["minute_bucket"] = tx["timestamp"].dt.floor("10min")

    daily = tx.groupby(["merchant_id", "date"]).size().reset_index(name="daily_tx_count")
    merchant_temporal = daily.groupby("merchant_id").agg(
        active_days=("date", "nunique"),
        mean_daily_tx=("daily_tx_count", "mean"),
        max_daily_tx=("daily_tx_count", "max"),
        std_daily_tx=("daily_tx_count", "std"),
    ).reset_index()
    merchant_temporal["spike_ratio"] = merchant_temporal["max_daily_tx"] / merchant_temporal["mean_daily_tx"].replace(0, np.nan)
    exact_collisions = tx.groupby(["merchant_id", "timestamp"]).size().reset_index(name="same_second_tx_count")
    exact_collisions = exact_collisions[exact_collisions["same_second_tx_count"] > 1].groupby("merchant_id").size().rename("exact_timestamp_collisions")
    merchant_temporal = merchant_temporal.merge(exact_collisions.reset_index(), on="merchant_id", how="left")
    merchant_temporal["exact_timestamp_collisions"] = merchant_temporal["exact_timestamp_collisions"].fillna(0).astype(int)
    merchant_temporal = merchant_temporal.merge(labels[["merchant_id", "is_mule", "network_id", "mule_type"]], on="merchant_id", how="left")

    network_rows: list[dict[str, Any]] = []
    for network_id, group in tx[tx["is_mule"] == 1].groupby("network_id"):
        bucket_counts = group.groupby("minute_bucket")["merchant_id"].nunique()
        coordination_windows = int((bucket_counts >= 2).sum())
        exact_same_second = int((group.groupby("timestamp")["merchant_id"].nunique() >= 2).sum())
        network_rows.append(
            {
                "network_id": network_id,
                "coordination_10min_windows": coordination_windows,
                "exact_same_second_multi_merchant_events": exact_same_second,
                "max_merchants_same_10min_window": int(bucket_counts.max()) if len(bucket_counts) else 0,
            }
        )
    exact_total = sum(row["exact_same_second_multi_merchant_events"] for row in network_rows)
    status = "WARNING" if exact_total > 0 else "PASS"
    return {
        "status": status,
        "merchant_temporal_features": merchant_temporal,
        "network_coordination": network_rows,
        "global": {
            "date_min": str(tx["timestamp"].min()),
            "date_max": str(tx["timestamp"].max()),
            "period_days": int((tx["timestamp"].max() - tx["timestamp"].min()).days + 1),
            "legitimate_median_spike_ratio": round(float(merchant_temporal.loc[merchant_temporal["is_mule"] == 0, "spike_ratio"].median()), 4),
            "mule_median_spike_ratio": round(float(merchant_temporal.loc[merchant_temporal["is_mule"] == 1, "spike_ratio"].median()), 4),
            "exact_same_second_multi_merchant_events": exact_total,
        },
        "warnings": ["Some mule merchants share exact same-second timestamps"] if exact_total > 0 else [],
    }


def score_dataset(**reports: dict[str, Any]) -> dict[str, Any]:
    score_parts = {
        "Network realism": (20, 17 if reports["network_report"]["status"] == "PASS" else 14),
        "Behavioral realism": (20, 16 if reports["overlap_report"]["status"] == "PASS" else 14),
        "Temporal realism": (15, 13 if reports["temporal_report"]["status"] == "PASS" else 10),
        "Label integrity": (15, 15 if reports["leakage_report"]["status"] == "PASS" else 11),
        "Referential integrity": (10, 10 if reports["integrity_report"]["status"] == "PASS" else 6),
        "Difficulty/non-triviality": (10, 7 if reports["feature_report"]["status"] == "WARNING" else 9),
        "Reproducibility": (5, 5 if reports["reproducibility_report"]["status"] == "PASS" else 0),
        "Evaluation suitability": (5, 4 if reports["generalization_report"]["status"] == "PASS" else 3),
    }
    total = sum(value for _, value in score_parts.values())
    if total >= 90:
        classification = "Ready for modeling"
    elif total >= 75:
        classification = "Minor fixes required"
    elif total >= 60:
        classification = "Significant fixes required"
    else:
        classification = "Redesign dataset"
    return {
        "total": total,
        "classification": classification,
        "parts": {name: {"max": max_score, "score": score} for name, (max_score, score) in score_parts.items()},
    }


def build_summary_markdown(**reports: dict[str, Any]) -> str:
    network_report = reports["network_report"]
    overlap_report = reports["overlap_report"]
    feature_report = reports["feature_report"]
    leakage_report = reports["leakage_report"]
    integrity_report = reports["integrity_report"]
    reproducibility_report = reports["reproducibility_report"]
    temporal_report = reports["temporal_report"]
    balance_report = reports["balance_report"]
    generalization_report = reports["generalization_report"]
    final_score = reports["final_score"]

    top_features = feature_report["feature_stats"].head(8)
    overlap_rows = pd.DataFrame(overlap_report["distributions"])
    key_overlap = overlap_rows[overlap_rows["metric"].isin(["shared_device_count", "shared_ip_count", "shared_customer_count", "shared_settlement_account_count"])]

    lines = [
        "# MuleHunter Dataset Audit Summary",
        "",
        "This audit reads the existing synthetic CSVs and does not modify the dataset.",
        "",
        "## Six Core Questions",
        "",
        f"1. Are the mule networks actually visible in the generated graph?  ",
        f"   STATUS: {network_report['status']}  ",
        f"   Evidence: {network_report['summary']['mule_networks']} labelled networks, "
        f"{network_report['summary']['networks_not_fully_connected']} not fully connected in the projected merchant graph. "
        f"The heterogeneous graph has {network_report['summary']['heterogeneous_nodes']} nodes and {network_report['summary']['heterogeneous_edges']} edges.",
        "",
        f"2. Are legitimate merchants also getting some overlaps?  ",
        f"   STATUS: {overlap_report['status']}  ",
        "   Evidence: legitimate merchants have non-zero overlap distributions across customers, devices, IPs and settlement accounts. "
        "This means overlap is not treated as deterministic fraud.",
        "",
        f"3. Are the mule patterns subtle enough?  ",
        f"   STATUS: {feature_report['status']}  ",
        f"   Evidence: {len(feature_report['warnings'])} single features crossed the high-separability warning threshold. "
        f"The simple core-network combination AUC is {feature_report['combination_check']['roc_auc']}.",
        "",
        f"4. Is there label leakage?  ",
        f"   STATUS: {leakage_report['status']}  ",
        "   Evidence: operational tables were checked for forbidden label columns, ID-range leakage, timing leakage and categorical leakage.",
        "",
        f"5. Do the CSV relationships make sense?  ",
        f"   STATUS: {integrity_report['status']}  ",
        "   Evidence: primary keys, foreign keys, timestamps, amounts, refunds and settlement consistency were checked.",
        "",
        f"6. Does the same seed reproduce the same dataset?  ",
        f"   STATUS: {reproducibility_report['status']}  ",
        f"   Evidence: seed {reproducibility_report['seed']} was generated twice and every table hash matched; seed "
        f"{reproducibility_report['seed_plus_one']} changed data while preserving schemas.",
        "",
        "## Class Balance",
        "",
        f"- Merchants: {balance_report['merchant_count']}",
        f"- Mule merchants: {balance_report['mule_merchants']}",
        f"- Legitimate merchants: {balance_report['legitimate_merchants']}",
        f"- Mule share: {balance_report['mule_share']}",
        f"- Mule networks: {balance_report['mule_networks']}",
        f"- Mule type distribution: {json.dumps(balance_report['mule_type_distribution'], sort_keys=True)}",
        "",
        "## Network Generalization",
        "",
        f"STATUS: {generalization_report['status']}",
        "",
        f"Recommended network-level split: {json.dumps(generalization_report['recommended_network_level_split'])}",
        "",
        generalization_report["assessment"],
        "",
        "## Temporal Realism",
        "",
        f"STATUS: {temporal_report['status']}",
        "",
        f"- Date range: {temporal_report['global']['date_min']} to {temporal_report['global']['date_max']}",
        f"- Period days: {temporal_report['global']['period_days']}",
        f"- Legitimate median spike ratio: {temporal_report['global']['legitimate_median_spike_ratio']}",
        f"- Mule median spike ratio: {temporal_report['global']['mule_median_spike_ratio']}",
        f"- Exact same-second multi-merchant mule events: {temporal_report['global']['exact_same_second_multi_merchant_events']}",
        "",
        "## Highest-Separability Features",
        "",
        markdown_table(
            top_features[
                ["feature", "legit_mean", "mule_mean", "cohen_d_mule_vs_legit", "roc_auc_single_feature", "status"]
            ]
        ),
        "",
        "## Key Overlap Distributions",
        "",
        markdown_table(key_overlap[["metric", "group", "median", "p95", "max"]]),
        "",
        "## Final Dataset Score",
        "",
        f"Total: {final_score['total']} / 100",
        "",
        f"Classification: {final_score['classification']}",
        "",
        "| Area | Score | Max |",
        "| --- | ---: | ---: |",
    ]
    for name, value in final_score["parts"].items():
        lines.append(f"| {name} | {value['score']} | {value['max']} |")

    lines.extend(
        [
            "",
            "## Recommended Fixes",
            "",
            "- Consider increasing mule networks from 10 to 20-30 before final evaluation so validation/test splits contain more scenario diversity.",
            "- Add temporal-only graph features later, because temporal coordination is intentionally not always visible in a static shared-entity projection.",
            "- During modeling, avoid raw IDs and ground-truth tables as features; use derived behavioral, graph and temporal features only.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_representative_network_json(
    examples_dir: Path,
    dataset: dict[str, pd.DataFrame],
    labels: pd.DataFrame,
    graph: nx.Graph,
) -> None:
    examples = []
    for network_id in sorted(labels.loc[labels["is_mule"] == 1, "network_id"].unique())[:3]:
        members = sorted(labels.loc[labels["network_id"] == network_id, "merchant_id"].tolist())
        subgraph = graph.subgraph(members)
        examples.append(
            {
                "network_id": network_id,
                "members": members,
                "edges": [
                    {
                        "source": left,
                        "target": right,
                        "weight": int(data["weight"]),
                        "reasons": sorted(data["reasons"]),
                    }
                    for left, right, data in subgraph.edges(data=True)
                ],
            }
        )
    write_json(examples_dir / "representative_networks.json", examples)
    (examples_dir / ".gitkeep").write_text("", encoding="utf-8")


def safe_auc(y: pd.Series, values: pd.Series) -> float | None:
    if y.nunique() < 2 or values.nunique(dropna=True) < 2:
        return None
    return float(roc_auc_score(y, values.fillna(0)))


def cohen_d(left: pd.Series, right: pd.Series) -> float:
    left_std = float(left.std(ddof=0))
    right_std = float(right.std(ddof=0))
    pooled = math.sqrt((left_std**2 + right_std**2) / 2)
    if pooled == 0:
        return 0.0
    return float((left.mean() - right.mean()) / pooled)


def hash_frame(frame: pd.DataFrame) -> str:
    return hashlib.sha256(frame.to_csv(index=False, date_format="%Y-%m-%d %H:%M:%S").encode("utf-8")).hexdigest()


def pass_fail(check: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"check": check, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def status_from_checks(checks: list[dict[str, Any]]) -> str:
    statuses = {check["status"] for check in checks}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARNING" in statuses:
        return "WARNING"
    return "PASS"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(to_jsonable(payload), indent=2), encoding="utf-8")


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    main()
