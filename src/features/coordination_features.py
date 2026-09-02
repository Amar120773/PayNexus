"""Extract relationship rarity and behavioral coordination features for MuleHunter."""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Mapping

def extract_coordination_features(
    dataset: Mapping[str, pd.DataFrame],
    merchants_df: pd.DataFrame,
    merchant_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Extract coordination and rarity features ensuring strict leakage boundaries.
    
    The function strictly filters transactions to `merchant_subset` BEFORE calculating 
    global entity frequencies to avoid test-set structural leakage.
    """
    
    tx = dataset["transactions"].copy()
    if merchant_subset is not None:
        tx = tx[tx["merchant_id"].isin(merchant_subset)].copy()
        target_merchants = pd.Series(merchant_subset)
    else:
        target_merchants = merchants_df["merchant_id"]
        
    if tx.empty:
        return pd.DataFrame({"merchant_id": target_merchants})
        
    features = pd.DataFrame({"merchant_id": target_merchants})
    
    # 1. RELATIONSHIP RARITY (Entity Frequencies)
    # Calculate how many unique merchants use each entity within the allowed subset
    ip_merchant_counts = tx.groupby("ip_id")["merchant_id"].nunique()
    device_merchant_counts = tx.groupby("device_id")["merchant_id"].nunique()
    customer_merchant_counts = tx.groupby("customer_id")["merchant_id"].nunique()
    
    # Map back to transactions
    tx["ip_merchant_count"] = tx["ip_id"].map(ip_merchant_counts)
    tx["device_merchant_count"] = tx["device_id"].map(device_merchant_counts)
    tx["customer_merchant_count"] = tx["customer_id"].map(customer_merchant_counts)
    
    # Rarity calculation for a merchant: 
    # Average rarity (1 / frequency) of entities used by the merchant. 
    # If a merchant only uses a dedicated IP (freq=1), rarity=1.0. 
    # If they use a shared IP (freq=100), rarity=0.01.
    tx["ip_rarity"] = 1.0 / tx["ip_merchant_count"]
    tx["device_rarity"] = 1.0 / tx["device_merchant_count"]
    tx["customer_rarity"] = 1.0 / tx["customer_merchant_count"]
    
    rarity_agg = tx.groupby("merchant_id").agg({
        "ip_rarity": "mean",
        "device_rarity": "mean",
        "customer_rarity": "mean",
        "ip_merchant_count": "mean",
        "device_merchant_count": "mean"
    }).reset_index()
    
    rarity_agg.rename(columns={
        "ip_rarity": "avg_ip_rarity",
        "device_rarity": "avg_device_rarity",
        "customer_rarity": "avg_customer_rarity",
        "ip_merchant_count": "avg_ip_frequency",
        "device_merchant_count": "avg_device_frequency"
    }, inplace=True)
    
    features = features.merge(rarity_agg, on="merchant_id", how="left").fillna(0.0)
    
    # 2. BEHAVIORAL COORDINATION (Shared Volume Ratio)
    # What % of a merchant's volume flows through shared entities?
    # Shared entity = used by >= 2 merchants
    tx["is_shared_ip"] = (tx["ip_merchant_count"] > 1).astype(int)
    tx["is_shared_device"] = (tx["device_merchant_count"] > 1).astype(int)
    tx["is_shared_customer"] = (tx["customer_merchant_count"] > 1).astype(int)
    
    vol_agg = tx.groupby("merchant_id").agg(
        total_tx_volume=("amount", "sum"),
        shared_ip_volume=("amount", lambda x: x[tx.loc[x.index, "is_shared_ip"] == 1].sum()),
        shared_device_volume=("amount", lambda x: x[tx.loc[x.index, "is_shared_device"] == 1].sum()),
        shared_customer_volume=("amount", lambda x: x[tx.loc[x.index, "is_shared_customer"] == 1].sum()),
    ).reset_index()
    
    vol_agg["shared_ip_volume_ratio"] = np.where(vol_agg["total_tx_volume"] > 0, vol_agg["shared_ip_volume"] / vol_agg["total_tx_volume"], 0.0)
    vol_agg["shared_device_volume_ratio"] = np.where(vol_agg["total_tx_volume"] > 0, vol_agg["shared_device_volume"] / vol_agg["total_tx_volume"], 0.0)
    vol_agg["shared_customer_volume_ratio"] = np.where(vol_agg["total_tx_volume"] > 0, vol_agg["shared_customer_volume"] / vol_agg["total_tx_volume"], 0.0)
    
    features = features.merge(vol_agg[["merchant_id", "shared_ip_volume_ratio", "shared_device_volume_ratio", "shared_customer_volume_ratio"]], on="merchant_id", how="left").fillna(0.0)
    
    # 3. TEMPORAL COORDINATION (Spike Sync)
    # Convert timestamps to days, and measure if merchant volume is concentrated in the same windows as their shared entities
    tx["tx_day"] = pd.to_datetime(tx["timestamp"]).dt.date
    
    # Daily volume for each merchant
    merchant_daily = tx.groupby(["merchant_id", "tx_day"])["amount"].sum().reset_index(name="daily_amount")
    
    # Calculate Gini coefficient of daily volume to represent "burstiness"
    def gini(array):
        array = np.array(array, dtype=np.float64)
        if len(array) == 0:
            return 0.0
        array = np.sort(array)
        index = np.arange(1, len(array) + 1)
        n = len(array)
        return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array) + 1e-8)
        
    burstiness = merchant_daily.groupby("merchant_id")["daily_amount"].agg(gini).reset_index(name="volume_burstiness")
    features = features.merge(burstiness, on="merchant_id", how="left").fillna(0.0)
    
    return features
