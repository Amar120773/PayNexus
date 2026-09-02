"""Network feature extraction for merchants in MuleHunter."""

from __future__ import annotations

from typing import Mapping

import networkx as nx
import numpy as np
import pandas as pd

from src.graph.build_graph import build_projected_merchant_graph


def extract_network_features(
    dataset: Mapping[str, pd.DataFrame],
    projected_graph: nx.Graph | None = None,
    merchants_df: pd.DataFrame | None = None,
    merchant_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Extract network topological and entity-sharing features for every merchant.

    CRITICAL: Does NOT use ground-truth labels (is_mule, mule_type, network_id).
    All features are computed purely from graph topology and entity co-occurrences.
    """
    if merchants_df is None:
        merchants = dataset["merchants"].copy()
    else:
        merchants = merchants_df.copy()
        
    if merchant_subset is not None:
        merchants = merchants[merchants["merchant_id"].isin(merchant_subset)]

    features = pd.DataFrame({"merchant_id": merchants["merchant_id"]})

    # 1. Direct Entity Sharing Counts
    for entity_col, source_table in [
        ("device_id", "transactions"),
        ("ip_id", "transactions"),
        ("customer_id", "transactions"),
        ("settlement_account_id", "settlements"),
    ]:
        col_name = "shared_settlement_count" if entity_col == "settlement_account_id" else f"shared_{entity_col.replace('_id', '')}_count"
        if source_table in dataset and entity_col in dataset[source_table].columns:
            source_df = dataset[source_table]
            if merchant_subset is not None:
                source_df = source_df[source_df["merchant_id"].isin(merchant_subset)]
            shared_df = _compute_shared_entity_counts(source_df, entity_col, target_col_name=col_name)
            features = features.merge(shared_df, on="merchant_id", how="left").fillna(0.0)
        else:
            features[col_name] = 0.0

    # 2. Build or use projected merchant graph
    if projected_graph is None:
        graph = build_projected_merchant_graph(dataset, merchant_subset=merchant_subset)
    else:
        graph = projected_graph

    # 3. Graph Topological Metrics
    degrees = dict(graph.degree())
    weighted_degrees = dict(graph.degree(weight="weight"))
    clustering = nx.clustering(graph)

    try:
        pagerank = nx.pagerank(graph, alpha=0.85, max_iter=200)
    except Exception:
        pagerank = {node: 1.0 / max(1, graph.number_of_nodes()) for node in graph.nodes}

    # Connected component sizes (network size)
    component_sizes: dict[str, int] = {}
    for comp in nx.connected_components(graph):
        c_size = len(comp)
        for node in comp:
            component_sizes[node] = c_size

    # Ego-network density
    ego_density: dict[str, float] = {}
    for node in graph.nodes:
        if degrees.get(node, 0) <= 1:
            ego_density[node] = 0.0
        else:
            ego_g = nx.ego_graph(graph, node)
            ego_density[node] = round(float(nx.density(ego_g)), 5)

    # Betweenness centrality (approximate if graph is large)
    try:
        betweenness = nx.betweenness_centrality(graph, normalized=True)
    except Exception:
        betweenness = {node: 0.0 for node in graph.nodes}

    features["connected_merchant_count"] = features["merchant_id"].map(degrees).fillna(0.0)
    features["merchant_degree"] = features["merchant_id"].map(degrees).fillna(0.0)
    features["weighted_network_degree"] = features["merchant_id"].map(weighted_degrees).fillna(0.0)
    features["network_size"] = features["merchant_id"].map(component_sizes).fillna(1.0)
    features["network_density"] = features["merchant_id"].map(ego_density).fillna(0.0)
    features["clustering_coefficient"] = features["merchant_id"].map(clustering).fillna(0.0)
    features["pagerank_score"] = features["merchant_id"].map(pagerank).fillna(0.0)
    features["betweenness_centrality"] = features["merchant_id"].map(betweenness).fillna(0.0)

    return features


def _compute_shared_entity_counts(df: pd.DataFrame, entity_col: str, target_col_name: str | None = None) -> pd.DataFrame:
    """Calculate the number of entities a merchant shares with at least one other merchant."""
    clean_pairs = df[["merchant_id", entity_col]].dropna().drop_duplicates()
    entity_to_merchants = clean_pairs.groupby(entity_col)["merchant_id"].nunique()
    shared_entities = set(entity_to_merchants[entity_to_merchants > 1].index)

    shared_pairs = clean_pairs[clean_pairs[entity_col].isin(shared_entities)]
    counts = shared_pairs.groupby("merchant_id")[entity_col].nunique()

    col_name = target_col_name if target_col_name else f"shared_{entity_col.replace('_id', '')}_count"
    return counts.rename(col_name).reset_index()


def compute_mule_labeled_neighbors(
    graph: nx.Graph,
    labels_df: pd.DataFrame,
) -> pd.DataFrame:
    """ANALYSIS ONLY: Compute number of mule-labeled neighbors in graph.

    WARNING: DO NOT use this feature in model training or prediction as it constitutes
    direct label leakage. This function is provided solely for diagnostic audits.
    """
    mule_merchants = set(labels_df[labels_df["is_mule"] == 1]["merchant_id"])
    records = []
    for node in graph.nodes:
        neighbors = set(graph.neighbors(node))
        mule_count = len(neighbors & mule_merchants)
        records.append({
            "merchant_id": node,
            "mule_labeled_neighbors_count": mule_count,
        })
    return pd.DataFrame(records)
