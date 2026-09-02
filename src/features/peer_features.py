"""Peer-relative feature extraction for context-aware anomaly detection."""

from __future__ import annotations
import itertools
import networkx as nx
import numpy as np
import pandas as pd
from typing import Mapping

def extract_peer_relative_features(
    dataset: Mapping[str, pd.DataFrame],
    merchants_df: pd.DataFrame,
    behavioral_features: pd.DataFrame,
    merchant_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Discover peer groups and compute Z-Scores relative to those peers."""
    tx = dataset["transactions"].copy()
    if merchant_subset is not None:
        tx = tx[tx["merchant_id"].isin(merchant_subset)].copy()
        target_merchants = pd.Series(merchant_subset)
    else:
        target_merchants = merchants_df["merchant_id"]

    if tx.empty:
        return pd.DataFrame({"merchant_id": target_merchants})
        
    features = pd.DataFrame({"merchant_id": target_merchants})
    
    # 1. Discover Peer Groups (Connected Components on Shared IP Graph)
    # We only use transactions in the valid subset!
    ip_to_merchants = tx.groupby("ip_id")["merchant_id"].unique()
    
    G = nx.Graph()
    G.add_nodes_from(target_merchants)
    
    for ip, connected_merchants in ip_to_merchants.items():
        if len(connected_merchants) > 1:
            # Add clique for shared IP
            G.add_edges_from(itertools.combinations(connected_merchants, 2))
            
    # Find components
    components = list(nx.connected_components(G))
    merchant_to_peer_group = {}
    for idx, comp in enumerate(components):
        for m in comp:
            merchant_to_peer_group[m] = idx
            
    peer_df = pd.DataFrame(list(merchant_to_peer_group.items()), columns=["merchant_id", "peer_group_id"])
    features = features.merge(peer_df, on="merchant_id", how="left")
    features["peer_group_id"] = features["peer_group_id"].fillna(-1).astype(int)
    
    # Calculate group sizes
    group_sizes = features.groupby("peer_group_id")["merchant_id"].count().reset_index(name="peer_group_size")
    features = features.merge(group_sizes, on="peer_group_id", how="left")
    
    # 2. Compute Z-Scores against peers
    # Merge behavioral features to calculate stats
    base_feats = behavioral_features[behavioral_features["merchant_id"].isin(target_merchants)]
    merged = features.merge(base_feats, on="merchant_id", how="left")
    
    columns_to_zscore = [
        "transaction_count", 
        "total_transaction_volume", 
        "average_transaction_amount",
        "refund_rate", 
        "failure_rate",
        "unique_customer_count"
    ]
    
    # Calculate means and stds per group
    group_stats = merged.groupby("peer_group_id")[columns_to_zscore].agg(["mean", "std"])
    
    for col in columns_to_zscore:
        mean_series = merged["peer_group_id"].map(group_stats[(col, "mean")])
        std_series = merged["peer_group_id"].map(group_stats[(col, "std")]).fillna(1e-6)
        std_series = np.where(std_series < 1e-6, 1e-6, std_series)
        
        features[f"{col}_zscore_vs_peers"] = (merged[col] - mean_series) / std_series
        # If group size is 1, z-score is 0
        features.loc[features["peer_group_size"] <= 1, f"{col}_zscore_vs_peers"] = 0.0

    return features[["merchant_id"] + [f"{c}_zscore_vs_peers" for c in columns_to_zscore]]
