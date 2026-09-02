"""Graph construction and analysis module for MuleHunter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import networkx as nx
import numpy as np
import pandas as pd


ENTITY_TABLE_MAP = {
    "customer_id": "customers",
    "device_id": "devices",
    "ip_id": "ips",
    "settlement_account_id": "settlement_accounts",
}


def load_graph_data(data_dir: Path | str = "data/synthetic") -> dict[str, pd.DataFrame]:
    """Load the synthetic datasets needed for graph construction."""
    data_path = Path(data_dir)
    tables = [
        "merchants",
        "customers",
        "devices",
        "ips",
        "settlement_accounts",
        "transactions",
        "settlements",
        "refunds",
    ]
    dataset: dict[str, pd.DataFrame] = {}
    for table in tables:
        file_path = data_path / f"{table}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Required table not found: {file_path}")
        dataset[table] = pd.read_csv(file_path)
    return dataset


def build_heterogeneous_graph(dataset: Mapping[str, pd.DataFrame], merchant_subset: list[str] | None = None) -> nx.Graph:
    """Construct heterogeneous relationship graph connecting merchants to entities.

    Nodes:
      - merchant:<merchant_id> (type: merchant)
      - customer_id:<customer_id> (type: customer_id)
      - device_id:<device_id> (type: device_id)
      - ip_id:<ip_id> (type: ip_id)
      - settlement_account_id:<account_id> (type: settlement_account_id)

    Edges:
      - merchant <-> customer
      - merchant <-> device
      - merchant <-> ip
      - merchant <-> settlement_account
    """
    graph = nx.Graph()

    # 1. Add Merchant nodes
    merchants_df = dataset["merchants"]
    if merchant_subset is not None:
        merchants_df = merchants_df[merchants_df["merchant_id"].isin(merchant_subset)]
        
    valid_merchants = set(merchants_df["merchant_id"])

    for _, row in merchants_df.iterrows():
        node_id = f"merchant:{row['merchant_id']}"
        graph.add_node(
            node_id,
            node_type="merchant",
            raw_id=row["merchant_id"],
            category=row.get("category", ""),
            kyc_status=row.get("kyc_status", ""),
        )

    # 2. Add Entity nodes
    for entity_col, table_name in ENTITY_TABLE_MAP.items():
        if table_name in dataset:
            entity_df = dataset[table_name]
            for entity_id in entity_df[entity_col].dropna().unique():
                node_id = f"{entity_col}:{entity_id}"
                graph.add_node(node_id, node_type=entity_col, raw_id=entity_id)

    # 3. Add Edges from Transactions (Merchant -> Customer, Device, IP)
    tx_df = dataset["transactions"]
    if merchant_subset is not None:
        tx_df = tx_df[tx_df["merchant_id"].isin(valid_merchants)]
        
    for entity_col in ["customer_id", "device_id", "ip_id"]:
        if entity_col in tx_df.columns:
            valid_tx = tx_df[["merchant_id", entity_col]].dropna()
            edge_counts = valid_tx.groupby(["merchant_id", entity_col]).size().reset_index(name="weight")
            for _, row in edge_counts.iterrows():
                u = f"merchant:{row['merchant_id']}"
                v = f"{entity_col}:{row[entity_col]}"
                if not graph.has_node(u):
                    graph.add_node(u, node_type="merchant", raw_id=row["merchant_id"])
                if not graph.has_node(v):
                    graph.add_node(v, node_type=entity_col, raw_id=row[entity_col])
                graph.add_edge(u, v, relationship=f"merchant_{entity_col}", weight=int(row["weight"]))

    # 4. Add Edges from Settlements (Merchant -> Settlement Account)
    settlements_df = dataset["settlements"]
    if merchant_subset is not None:
        settlements_df = settlements_df[settlements_df["merchant_id"].isin(valid_merchants)]
        
    if "settlement_account_id" in settlements_df.columns:
        valid_settlements = settlements_df[["merchant_id", "settlement_account_id"]].dropna()
        settlement_counts = valid_settlements.groupby(["merchant_id", "settlement_account_id"]).size().reset_index(name="weight")
        for _, row in settlement_counts.iterrows():
            u = f"merchant:{row['merchant_id']}"
            v = f"settlement_account_id:{row['settlement_account_id']}"
            if not graph.has_node(u):
                graph.add_node(u, node_type="merchant", raw_id=row["merchant_id"])
            if not graph.has_node(v):
                graph.add_node(v, node_type="settlement_account_id", raw_id=row["settlement_account_id"])
            graph.add_edge(u, v, relationship="merchant_settlement_account", weight=int(row["weight"]))

    return graph


def build_projected_merchant_graph(dataset: Mapping[str, pd.DataFrame], merchant_subset: list[str] | None = None) -> nx.Graph:
    """Construct projected merchant-to-merchant relationship graph.

    Two merchants have an edge if they share at least one device, IP, customer,
    or settlement account.
    """
    graph = nx.Graph()
    merchants_df = dataset["merchants"]
    if merchant_subset is not None:
        merchants = [m for m in merchants_df["merchant_id"].unique() if m in merchant_subset]
    else:
        merchants = merchants_df["merchant_id"].unique()
        
    valid_merchants = set(merchants)
    for m in merchants:
        graph.add_node(m, raw_id=m)

    def _add_co_occurrences(df: pd.DataFrame, entity_col: str, reason_name: str) -> None:
        if entity_col not in df.columns or "merchant_id" not in df.columns:
            return
        unique_pairs = df[["merchant_id", entity_col]].dropna().drop_duplicates()
        grouped = unique_pairs.groupby(entity_col)["merchant_id"].apply(list)
        for _, merchant_list in grouped.items():
            unique_m = sorted(set(merchant_list))
            if len(unique_m) < 2:
                continue
            for i in range(len(unique_m)):
                for j in range(i + 1, len(unique_m)):
                    m1, m2 = unique_m[i], unique_m[j]
                    if not graph.has_edge(m1, m2):
                        graph.add_edge(
                            m1,
                            m2,
                            weight=0,
                            reasons=set(),
                            shared_devices=0,
                            shared_ips=0,
                            shared_customers=0,
                            shared_settlements=0,
                        )
                    graph[m1][m2]["weight"] += 1
                    graph[m1][m2]["reasons"].add(reason_name)
                    if reason_name == "device":
                        graph[m1][m2]["shared_devices"] += 1
                    elif reason_name == "ip":
                        graph[m1][m2]["shared_ips"] += 1
                    elif reason_name == "customer":
                        graph[m1][m2]["shared_customers"] += 1
                    elif reason_name == "settlement":
                        graph[m1][m2]["shared_settlements"] += 1

    tx = dataset["transactions"]
    if merchant_subset is not None:
        tx = tx[tx["merchant_id"].isin(valid_merchants)]
        
    _add_co_occurrences(tx, "device_id", "device")
    _add_co_occurrences(tx, "ip_id", "ip")
    _add_co_occurrences(tx, "customer_id", "customer")

    settlements = dataset["settlements"]
    if merchant_subset is not None:
        settlements = settlements[settlements["merchant_id"].isin(valid_merchants)]
        
    _add_co_occurrences(settlements, "settlement_account_id", "settlement")

    return graph


def compute_graph_statistics(
    hetero_graph: nx.Graph,
    projected_graph: nx.Graph | None = None,
) -> dict[str, Any]:
    """Calculate comprehensive graph statistics for reporting."""
    # 1. Node type breakdown
    node_types: dict[str, int] = {}
    for _, attrs in hetero_graph.nodes(data=True):
        nt = attrs.get("node_type", "unknown")
        node_types[nt] = node_types.get(nt, 0) + 1

    # 2. Edge relationship breakdown
    edge_relationships: dict[str, int] = {}
    for _, _, attrs in hetero_graph.edges(data=True):
        rel = attrs.get("relationship", "unknown")
        edge_relationships[rel] = edge_relationships.get(rel, 0) + 1

    # 3. Connected components in heterogeneous graph
    hetero_components = list(nx.connected_components(hetero_graph))
    component_sizes = [len(c) for c in hetero_components]
    component_sizes.sort(reverse=True)

    # 4. Merchant degree stats in heterogeneous graph
    merchant_nodes = [n for n, attrs in hetero_graph.nodes(data=True) if attrs.get("node_type") == "merchant"]
    merchant_degrees = [hetero_graph.degree(m) for m in merchant_nodes] if merchant_nodes else [0]

    stats: dict[str, Any] = {
        "heterogeneous_graph": {
            "num_nodes": hetero_graph.number_of_nodes(),
            "num_edges": hetero_graph.number_of_edges(),
            "nodes_by_type": node_types,
            "edges_by_relationship": edge_relationships,
            "connected_components_count": len(hetero_components),
            "largest_components_sizes": component_sizes[:10],
            "merchant_degree_statistics": {
                "min": int(np.min(merchant_degrees)),
                "max": int(np.max(merchant_degrees)),
                "mean": round(float(np.mean(merchant_degrees)), 2),
                "median": float(np.median(merchant_degrees)),
                "std": round(float(np.std(merchant_degrees)), 2),
            },
        }
    }

    # 5. Projected graph statistics
    if projected_graph is not None:
        proj_components = list(nx.connected_components(projected_graph))
        proj_comp_sizes = [len(c) for c in proj_components]
        proj_comp_sizes.sort(reverse=True)
        proj_degrees = [d for _, d in projected_graph.degree()] if projected_graph.nodes else [0]
        isolated_merchants = sum(1 for d in proj_degrees if d == 0)

        stats["projected_merchant_graph"] = {
            "num_merchants": projected_graph.number_of_nodes(),
            "num_edges": projected_graph.number_of_edges(),
            "density": round(float(nx.density(projected_graph)), 5),
            "connected_components_count": len(proj_components),
            "largest_components_sizes": proj_comp_sizes[:10],
            "isolated_merchants": isolated_merchants,
            "merchant_degree_statistics": {
                "min": int(np.min(proj_degrees)),
                "max": int(np.max(proj_degrees)),
                "mean": round(float(np.mean(proj_degrees)), 2),
                "median": float(np.median(proj_degrees)),
                "std": round(float(np.std(proj_degrees)), 2),
            },
        }

    return stats


def save_graph_statistics(stats: dict[str, Any], output_path: Path | str = "reports/graph_statistics.json") -> None:
    """Save graph statistics dictionary to a JSON report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def main() -> None:
    """Run graph construction and statistics generation."""
    print("Building MuleHunter relationship graphs...")
    dataset = load_graph_data("data/synthetic")
    hetero_graph = build_heterogeneous_graph(dataset)
    projected_graph = build_projected_merchant_graph(dataset)
    stats = compute_graph_statistics(hetero_graph, projected_graph)
    save_graph_statistics(stats, "reports/graph_statistics.json")
    print(f"Graph construction complete.")
    print(f"Heterogeneous Graph: {hetero_graph.number_of_nodes()} nodes, {hetero_graph.number_of_edges()} edges")
    print(f"Projected Merchant Graph: {projected_graph.number_of_nodes()} nodes, {projected_graph.number_of_edges()} edges")
    print("Saved statistics to reports/graph_statistics.json")


if __name__ == "__main__":
    main()
