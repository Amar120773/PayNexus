import pandas as pd
import numpy as np
import networkx as nx
import json
from collections import defaultdict
import os

print("Loading data...")
tx = pd.read_csv("data/synthetic/transactions.csv")
tx["timestamp"] = pd.to_datetime(tx["timestamp"])
merchants = pd.read_csv("data/synthetic/merchants.csv")
labels = pd.read_csv("data/processed/merchant_labels.csv") if os.path.exists("data/processed/merchant_labels.csv") else pd.read_csv("data/synthetic/merchant_labels.csv")

# Get start date and define periods
start_date = tx["timestamp"].min().normalize()
t1_end = start_date + pd.Timedelta(days=30)
t2_end = start_date + pd.Timedelta(days=60)
t3_end = start_date + pd.Timedelta(days=90)

print(f"T1: {start_date} to {t1_end}")
print(f"T2: {t1_end} to {t2_end}")
print(f"T3: {t2_end} to {t3_end}")

tx_t1 = tx[tx["timestamp"] < t1_end]
tx_t2 = tx[(tx["timestamp"] >= t1_end) & (tx["timestamp"] < t2_end)]
tx_t3 = tx[(tx["timestamp"] >= t2_end) & (tx["timestamp"] < t3_end)]

# To group merchants into networks, we'll use the IP clusters logic from our recent experiments 
# since that's how we define a "benign shared-infrastructure network".
# We also have ground truth `network_id` for mules.
# Let's identify the clusters globally first, then track their evolution.
ip_merchants = tx.groupby("ip_id")["merchant_id"].unique()
valid_clusters = ip_merchants[ip_merchants.apply(len) >= 3].to_dict()

# We want to compare Mule Networks vs Benign Infrastructure Networks
# Let's get the mules
mule_merchants = labels[labels["is_mule"] == 1]["merchant_id"].unique()
mule_networks = labels[labels["is_mule"] == 1].groupby("network_id")["merchant_id"].unique().to_dict()

# Let's define Benign Networks as clusters of size >= 3 that have 0 mules.
benign_networks = {}
b_idx = 1
for ip, m_list in valid_clusters.items():
    if not any(m in mule_merchants for m in m_list):
        benign_networks[f"B{b_idx:03d}"] = list(m_list)
        b_idx += 1

print(f"Found {len(mule_networks)} Mule Networks and {len(benign_networks)} Benign Networks")

def calculate_snapshot_metrics(tx_subset: pd.DataFrame, network_merchants: list) -> dict:
    net_tx = tx_subset[tx_subset["merchant_id"].isin(network_merchants)]
    if net_tx.empty:
        return {
            "merchant_nodes": 0, "merchant_edges": 0, "shared_devices": 0, "shared_ips": 0, 
            "shared_customers": 0, "transaction_volume": 0, "refund_rate": 0, "avg_ticket": 0
        }
        
    merchants_active = net_tx["merchant_id"].nunique()
    
    # Bipartite edges
    shared_devices = (net_tx.groupby("device_id")["merchant_id"].nunique() > 1).sum()
    shared_ips = (net_tx.groupby("ip_id")["merchant_id"].nunique() > 1).sum()
    shared_custs = (net_tx.groupby("customer_id")["merchant_id"].nunique() > 1).sum()
    
    # Graph edges
    G = nx.Graph()
    for col in ["device_id", "ip_id"]:
        for entity, group in net_tx.groupby(col)["merchant_id"].unique().items():
            if len(group) > 1:
                import itertools
                G.add_edges_from(itertools.combinations(group, 2))
                
    edges = G.number_of_edges()
    
    volume = net_tx["amount"].sum()
    refund_rate = (net_tx["status"] == "REFUNDED").mean()
    avg_ticket = net_tx["amount"].mean()
    
    return {
        "merchant_nodes": merchants_active,
        "merchant_edges": edges,
        "shared_devices": shared_devices,
        "shared_ips": shared_ips,
        "shared_customers": shared_custs,
        "transaction_volume": volume,
        "refund_rate": refund_rate,
        "avg_ticket": avg_ticket
    }

results = []

for is_mule, networks in [(True, mule_networks), (False, benign_networks)]:
    for net_id, members in networks.items():
        m1 = calculate_snapshot_metrics(tx_t1, members)
        m2 = calculate_snapshot_metrics(tx_t2, members)
        m3 = calculate_snapshot_metrics(tx_t3, members)
        
        # Calculate Deltas (T2-T1 and T3-T2)
        def delta(a, b):
            return b - a
            
        row = {
            "network_id": net_id,
            "is_mule": is_mule,
            "merchant_count": len(members),
            # T1 Metrics
            "t1_nodes": m1["merchant_nodes"],
            "t1_edges": m1["merchant_edges"],
            "t1_volume": m1["transaction_volume"],
            "t1_refund_rate": m1["refund_rate"],
            # T2 Metrics
            "t2_nodes": m2["merchant_nodes"],
            "t2_edges": m2["merchant_edges"],
            "t2_volume": m2["transaction_volume"],
            "t2_refund_rate": m2["refund_rate"],
            # T3 Metrics
            "t3_nodes": m3["merchant_nodes"],
            "t3_edges": m3["merchant_edges"],
            "t3_volume": m3["transaction_volume"],
            "t3_refund_rate": m3["refund_rate"],
            
            # Deltas T1->T2
            "delta_nodes_t1_t2": delta(m1["merchant_nodes"], m2["merchant_nodes"]),
            "delta_edges_t1_t2": delta(m1["merchant_edges"], m2["merchant_edges"]),
            "delta_volume_t1_t2": delta(m1["transaction_volume"], m2["transaction_volume"]),
            "delta_refund_t1_t2": delta(m1["refund_rate"], m2["refund_rate"]),
            
            # Deltas T2->T3
            "delta_nodes_t2_t3": delta(m2["merchant_nodes"], m3["merchant_nodes"]),
            "delta_edges_t2_t3": delta(m2["merchant_edges"], m3["merchant_edges"]),
            "delta_volume_t2_t3": delta(m2["transaction_volume"], m3["transaction_volume"]),
            "delta_refund_t2_t3": delta(m2["refund_rate"], m3["refund_rate"]),
        }
        results.append(row)

df = pd.DataFrame(results)
df.to_csv("reports/network_evolution_features.csv", index=False)

print("Analysis complete. CSV saved to reports/network_evolution_features.csv")

# Summarize for report
summary = df.groupby("is_mule").agg({
    "delta_nodes_t1_t2": "mean",
    "delta_edges_t1_t2": "mean",
    "delta_volume_t1_t2": "mean",
    "delta_refund_t1_t2": "mean",
    "delta_nodes_t2_t3": "mean",
    "delta_edges_t2_t3": "mean",
    "delta_volume_t2_t3": "mean",
    "delta_refund_t2_t3": "mean",
}).T
print(summary)
