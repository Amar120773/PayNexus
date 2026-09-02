"""Feature extraction for Network Evolution Intelligence."""

from __future__ import annotations
import pandas as pd
import numpy as np
import networkx as nx

def extract_evolution_features(
    merchants: pd.DataFrame,
    transactions: pd.DataFrame,
    relationships: pd.DataFrame,
    scoring_timestamp_str: str,
    valid_merchants: list[str] | None = None
) -> pd.DataFrame:
    """Extract temporal trajectory features for merchants across T1, T2, T3 relative to scoring_timestamp_str."""
    
    scoring_ts = pd.Timestamp(scoring_timestamp_str)
    
    # Strict temporal leakage protection
    if "timestamp" in transactions.columns:
        tx = transactions[transactions["timestamp"] <= scoring_ts].copy()
    else:
        tx = transactions.copy()
        
    rels = relationships[relationships["start_time"] <= scoring_ts].copy()
    
    # Time windows backward from scoring_ts
    t3_end = scoring_ts
    t2_end = scoring_ts - pd.Timedelta(days=30)
    t1_end = scoring_ts - pd.Timedelta(days=60)
    t0_start = scoring_ts - pd.Timedelta(days=90)
    
    if valid_merchants is not None:
        target_merchants = valid_merchants
        tx_target = tx[tx["merchant_id"].isin(valid_merchants)]
    else:
        target_merchants = merchants["merchant_id"].unique()
        tx_target = tx
        
    def _compute_snapshot(tx_window_target, rels_window, end_ts):
        # 1. Behavioral aggregations (for target merchants)
        vol = tx_window_target.groupby("merchant_id")["amount"].sum().reindex(target_merchants, fill_value=0.0)
        
        status_counts = tx_window_target.groupby(["merchant_id", "status"]).size().unstack(fill_value=0)
        refunds = status_counts.get("REFUNDED", pd.Series(0, index=status_counts.index))
        total_tx = status_counts.sum(axis=1)
        refund_rate = (refunds / total_tx).reindex(target_merchants, fill_value=0.0)
        refund_rate = refund_rate.fillna(0.0)
        
        # 2. Structural aggregations (Global for graph, local for sets)
        window_start = end_ts - pd.Timedelta(days=30)
        active_rels = rels_window[(rels_window["start_time"] < end_ts) & (rels_window["end_time"] > window_start)]
        
        active_rels_target = active_rels[active_rels["merchant_id"].isin(target_merchants)]
        dev_rels = active_rels_target[active_rels_target["entity_type"] == "device"]
        ip_rels = active_rels_target[active_rels_target["entity_type"] == "ip"]
        
        dev_sets = dev_rels.groupby("merchant_id")["entity_id"].apply(set).reindex(target_merchants, fill_value=set())
        ip_sets = ip_rels.groupby("merchant_id")["entity_id"].apply(set).reindex(target_merchants, fill_value=set())
        
        # Network size (1-hop shared infrastructure) built on FULL active_rels
        G = nx.Graph()
        all_merchants_in_window = active_rels["merchant_id"].unique()
        G.add_nodes_from(all_merchants_in_window, bipartite=0)
        
        edges = []
        for _, row in active_rels.iterrows():
            edges.append((row["merchant_id"], row["entity_id"]))
            
        G.add_edges_from(edges)
        
        network_size = pd.Series(0, index=target_merchants)
        
        for m in target_merchants:
            if m in G:
                shared_merchants = set()
                for entity in G.neighbors(m):
                    for neighbor_m in G.neighbors(entity):
                        if neighbor_m != m:
                            shared_merchants.add(neighbor_m)
                network_size[m] = len(shared_merchants)
                
        return pd.DataFrame({
            "volume": vol,
            "refund_rate": refund_rate,
            "devices": dev_sets,
            "ips": ip_sets,
            "network_size": network_size
        })

    # T1
    tx_t1_target = tx_target[(tx_target["timestamp"] >= t0_start) & (tx_target["timestamp"] < t1_end)]
    s1 = _compute_snapshot(tx_t1_target, rels, t1_end)
    
    # T2
    tx_t2_target = tx_target[(tx_target["timestamp"] >= t1_end) & (tx_target["timestamp"] < t2_end)]
    s2 = _compute_snapshot(tx_t2_target, rels, t2_end)
    
    # T3
    tx_t3_target = tx_target[(tx_target["timestamp"] >= t2_end) & (tx_target["timestamp"] < t3_end)]
    s3 = _compute_snapshot(tx_t3_target, rels, t3_end)
    
    def churn_rate(set1, set2):
        res = pd.Series(0.0, index=set1.index)
        for idx in set1.index:
            s1_set, s2_set = set1[idx], set2[idx]
            if not s1_set and not s2_set: continue
            diff = len(s1_set.symmetric_difference(s2_set))
            res[idx] = diff / max(len(s1_set.union(s2_set)), 1)
        return res
        
    df = pd.DataFrame(index=target_merchants)
    df.index.name = "merchant_id"
    
    # T1->T2 Deltas
    df["volume_delta_t1_t2"] = s2["volume"] - s1["volume"]
    df["refund_delta_t1_t2"] = s2["refund_rate"] - s1["refund_rate"]
    df["network_growth_t1_t2"] = s2["network_size"] - s1["network_size"]
    df["device_churn_t1_t2"] = churn_rate(s1["devices"], s2["devices"])
    df["ip_churn_t1_t2"] = churn_rate(s1["ips"], s2["ips"])
    
    # T2->T3 Deltas
    df["volume_delta_t2_t3"] = s3["volume"] - s2["volume"]
    df["refund_delta_t2_t3"] = s3["refund_rate"] - s2["refund_rate"]
    df["network_growth_t2_t3"] = s3["network_size"] - s2["network_size"]
    df["device_churn_t2_t3"] = churn_rate(s2["devices"], s3["devices"])
    df["ip_churn_t2_t3"] = churn_rate(s2["ips"], s3["ips"])
    
    # Static T3 Baseline Features
    df["volume_static_t3"] = s3["volume"]
    df["refund_rate_static_t3"] = s3["refund_rate"]
    df["network_size_static_t3"] = s3["network_size"]
    
    return df.reset_index()
