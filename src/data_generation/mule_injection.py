"""Mule-network scenario injection for synthetic merchant data (Camouflaged inside Benign Clusters)."""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from src.data_generation.config import MULE_SCENARIOS, SyntheticDataConfig

@dataclass(frozen=True)
class MuleInjectionResult:
    transactions: pd.DataFrame
    merchant_settlement_accounts: pd.Series
    merchant_labels: pd.DataFrame
    mule_networks: pd.DataFrame

def inject_mule_networks(
    *,
    config: SyntheticDataConfig,
    rng: np.random.Generator,
    merchants: pd.DataFrame,
    transactions: pd.DataFrame,
    customer_ids: np.ndarray,
    device_ids: np.ndarray,
    ip_ids: np.ndarray,
    settlement_account_ids: np.ndarray,
    merchant_settlement_accounts: pd.Series,
) -> MuleInjectionResult:
    """Inject mules by hijacking existing benign infrastructure clusters and altering their behavior."""
    
    tx = transactions.copy()
    account_map = merchant_settlement_accounts.copy()
    
    # 1. Identify Benign Clusters
    # We define a benign cluster as merchants sharing the exact same IP.
    # Group by IP, find IPs with between 3 and 10 merchants.
    ip_merchants = tx.groupby("ip_id")["merchant_id"].unique()
    valid_clusters = ip_merchants[(ip_merchants.apply(len) >= 3) & (ip_merchants.apply(len) <= 10)].tolist()
    
    # Shuffle and pick `config.mule_networks` clusters
    # Fallback to random groupings if not enough clusters
    if len(valid_clusters) < config.mule_networks:
        available_merchants = tx["merchant_id"].unique()
        needed = config.mule_networks - len(valid_clusters)
        for _ in range(needed):
            cluster_size = rng.integers(3, 8)
            valid_clusters.append(rng.choice(available_merchants, size=cluster_size, replace=False))
            
    chosen_clusters = [valid_clusters[i] for i in rng.choice(len(valid_clusters), size=config.mule_networks, replace=False)]
    
    label_rows: list[dict[str, object]] = []
    network_rows: list[dict[str, object]] = []
    
    for index, cluster_merchants in enumerate(chosen_clusters, start=1):
        network_id = f"N{index:03d}"
        
        # Pick 1 or 2 mules inside this benign cluster
        num_mules = min(2, len(cluster_merchants) - 1)
        if num_mules < 1:
            num_mules = 1
        mules = rng.choice(cluster_merchants, size=num_mules, replace=False)
        
        primary = MULE_SCENARIOS[(index - 1) % len(MULE_SCENARIOS)]
        
        if primary == "ABNORMAL_VOLUME_SPIKE":
            _apply_volume_spike(tx, mules, rng)
        elif primary == "ABNORMAL_REFUND_RATE":
            _apply_abnormal_refunds(tx, mules, rng)
        elif primary == "ABNORMAL_FAILURE_RATE":
            _apply_abnormal_failures(tx, mules, rng)
        elif primary == "ABNORMAL_TICKET_SIZE":
            _apply_abnormal_tickets(tx, mules, rng)
            
        for merchant_id in mules:
            label_rows.append({
                "merchant_id": merchant_id,
                "network_id": network_id,
                "is_mule": 1,
                "mule_type": primary,
            })
            
        network_rows.append({
            "network_id": network_id,
            "primary_mule_type": primary,
            "patterns": primary,
            "merchant_count": len(mules),
            "cluster_size": len(cluster_merchants),
        })

    mule_label_frame = pd.DataFrame(label_rows).drop_duplicates(subset=["merchant_id"])
    labels = merchants[["merchant_id"]].merge(mule_label_frame, on="merchant_id", how="left")
    labels["is_mule"] = labels["is_mule"].fillna(0).astype(int)
    labels["network_id"] = labels["network_id"].fillna("")
    labels["mule_type"] = labels["mule_type"].fillna("")

    tx = tx.sort_values("transaction_id").reset_index(drop=True)
    return MuleInjectionResult(
        transactions=tx,
        merchant_settlement_accounts=account_map,
        merchant_labels=labels,
        mule_networks=pd.DataFrame(network_rows),
    )

def _apply_volume_spike(tx: pd.DataFrame, members: np.ndarray, rng: np.random.Generator) -> None:
    # Shift 80% of transactions to a single 2-day window
    for merchant_id in members:
        idx = tx.index[tx["merchant_id"] == merchant_id].to_numpy()
        if len(idx) == 0: continue
        spike_start = pd.Timestamp("2026-02-01") + pd.Timedelta(days=int(rng.integers(0, 60)))
        spike_idx = rng.choice(idx, size=int(len(idx) * 0.8), replace=False)
        random_offsets = pd.to_timedelta(rng.integers(0, 48, size=len(spike_idx)), unit="h")
        new_times = spike_start + random_offsets
        tx.loc[spike_idx, "timestamp"] = new_times.strftime("%Y-%m-%d %H:%M:%S")

def _apply_abnormal_refunds(tx: pd.DataFrame, members: np.ndarray, rng: np.random.Generator) -> None:
    # Set refund rate to 40-70% (way above normal 1-5%)
    for merchant_id in members:
        idx = tx.index[tx["merchant_id"] == merchant_id].to_numpy()
        if len(idx) == 0: continue
        refund_idx = rng.choice(idx, size=int(len(idx) * rng.uniform(0.4, 0.7)), replace=False)
        tx.loc[refund_idx, "status"] = "REFUNDED"
        
def _apply_abnormal_failures(tx: pd.DataFrame, members: np.ndarray, rng: np.random.Generator) -> None:
    # Set failure rate to 60-90%
    for merchant_id in members:
        idx = tx.index[tx["merchant_id"] == merchant_id].to_numpy()
        if len(idx) == 0: continue
        fail_idx = rng.choice(idx, size=int(len(idx) * rng.uniform(0.6, 0.9)), replace=False)
        tx.loc[fail_idx, "status"] = "FAILED"

def _apply_abnormal_tickets(tx: pd.DataFrame, members: np.ndarray, rng: np.random.Generator) -> None:
    # Multiply all transaction amounts by 15x
    for merchant_id in members:
        idx = tx.index[tx["merchant_id"] == merchant_id].to_numpy()
        if len(idx) == 0: continue
        tx.loc[idx, "amount"] = (tx.loc[idx, "amount"] * rng.uniform(10.0, 20.0)).round(2)
