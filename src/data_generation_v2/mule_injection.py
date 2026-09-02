"""Mule-network scenario injection for temporal evolution (Dataset V2)."""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from src.data_generation_v2.config import MULE_SCENARIOS, SyntheticDataConfig
from src.data_generation_v2.events import get_event_logger

@dataclass(frozen=True)
class MuleInjectionResult:
    transactions: pd.DataFrame
    merchant_labels: pd.DataFrame
    mule_networks: pd.DataFrame
    relationships: pd.DataFrame

def inject_mule_networks(
    *,
    config: SyntheticDataConfig,
    rng: np.random.Generator,
    merchants: pd.DataFrame,
    transactions: pd.DataFrame,
    relationships: pd.DataFrame,
) -> MuleInjectionResult:
    tx = transactions.copy()
    rels = relationships.copy()
    logger = get_event_logger()
    
    start_ts = pd.Timestamp(config.start_date)
    end_ts = start_ts + pd.Timedelta(days=config.period_days)
    
    available_merchants = merchants["merchant_id"].to_numpy()
    mule_merchants = rng.choice(available_merchants, size=min(len(available_merchants), config.mule_networks * 4), replace=False)
    
    label_rows: list[dict[str, object]] = []
    network_rows: list[dict[str, object]] = []
    
    cursor = 0
    for index in range(1, config.mule_networks + 1):
        network_id = f"N{index:03d}"
        size = int(rng.integers(3, 8))
        if cursor + size > len(mule_merchants):
            break
        
        members = mule_merchants[cursor : cursor + size]
        cursor += size
        
        primary = MULE_SCENARIOS[(index - 1) % len(MULE_SCENARIOS)]
        
        if primary == "TYPE_A_RAPID_FORMATION":
            rels, tx = _apply_rapid_formation(members, rels, tx, start_ts, end_ts, rng, logger)
        elif primary == "TYPE_B_GRADUAL_EXPANSION":
            rels, tx = _apply_gradual_expansion(members, rels, tx, start_ts, end_ts, rng, logger)
        elif primary == "TYPE_C_INFRASTRUCTURE_CONVERGENCE":
            rels, tx = _apply_infrastructure_convergence(members, rels, tx, start_ts, end_ts, rng, logger)
        elif primary == "TYPE_D_BEHAVIORAL_TRANSITION":
            tx = _apply_behavioral_transition(members, tx, start_ts, end_ts, rng)
            
        for merchant_id in members:
            label_rows.append({"merchant_id": merchant_id, "network_id": network_id, "is_mule": 1, "mule_type": primary})
            
        network_rows.append({"network_id": network_id, "primary_mule_type": primary, "merchant_count": len(members)})

    mule_label_frame = pd.DataFrame(label_rows)
    if not mule_label_frame.empty:
        labels = merchants[["merchant_id"]].merge(mule_label_frame, on="merchant_id", how="left")
        labels["is_mule"] = labels["is_mule"].fillna(0).astype(int)
        labels["network_id"] = labels["network_id"].fillna("")
        labels["mule_type"] = labels["mule_type"].fillna("")
    else:
        labels = merchants[["merchant_id"]].copy()
        labels["is_mule"] = 0
        labels["network_id"] = ""
        labels["mule_type"] = ""

    tx = tx.sort_values("timestamp").reset_index(drop=True)
    return MuleInjectionResult(transactions=tx, merchant_labels=labels, mule_networks=pd.DataFrame(network_rows), relationships=rels)

def _apply_rapid_formation(members, rels, tx, start_ts, end_ts, rng, logger):
    # Members all connect to a single IP rapidly within a 3-day window
    shared_ip = f"I_MULE_{rng.integers(1, 1000):04d}"
    formation_date = start_ts + pd.Timedelta(days=rng.integers(20, 70))
    
    new_rels = []
    for m in members:
        # Close old IP relations
        mask = (rels["merchant_id"] == m) & (rels["entity_type"] == "ip") & (rels["end_time"] > formation_date)
        rels.loc[mask, "end_time"] = formation_date
        join_date = formation_date + pd.Timedelta(hours=rng.integers(0, 72))
        new_rels.append({"merchant_id": m, "entity_type": "ip", "entity_id": shared_ip, "start_time": join_date, "end_time": end_ts})
        logger.log(join_date, m, "NETWORK_JOINED", shared_ip)
        
    rels = pd.concat([rels, pd.DataFrame(new_rels)], ignore_index=True)
    
    # Also synchronize a volume spike
    for m in members:
        idx = tx.index[tx["merchant_id"] == m].to_numpy()
        if len(idx) > 0:
            spike_idx = rng.choice(idx, size=int(len(idx) * 0.7), replace=False)
            offsets = pd.to_timedelta(rng.integers(0, 72, size=len(spike_idx)), unit="h")
            tx.loc[spike_idx, "timestamp"] = formation_date + offsets
            
    return rels, tx

def _apply_gradual_expansion(members, rels, tx, start_ts, end_ts, rng, logger):
    # Members connect to a shared IP sequentially over 40 days
    shared_ip = f"I_MULE_{rng.integers(1, 1000):04d}"
    base_date = start_ts + pd.Timedelta(days=rng.integers(10, 30))
    
    new_rels = []
    for i, m in enumerate(members):
        join_date = base_date + pd.Timedelta(days=int(i * (40 / len(members))))
        mask = (rels["merchant_id"] == m) & (rels["entity_type"] == "ip") & (rels["end_time"] > join_date)
        rels.loc[mask, "end_time"] = join_date
        new_rels.append({"merchant_id": m, "entity_type": "ip", "entity_id": shared_ip, "start_time": join_date, "end_time": end_ts})
        logger.log(join_date, m, "NETWORK_JOINED", shared_ip)
        
    rels = pd.concat([rels, pd.DataFrame(new_rels)], ignore_index=True)
    return rels, tx

def _apply_infrastructure_convergence(members, rels, tx, start_ts, end_ts, rng, logger):
    # Members swap to the exact same IP and Device at roughly the same time
    shared_ip = f"I_MULE_{rng.integers(1, 1000):04d}"
    shared_dev = f"D_MULE_{rng.integers(1, 1000):04d}"
    conv_date = start_ts + pd.Timedelta(days=rng.integers(30, 60))
    
    new_rels = []
    for m in members:
        mask_ip = (rels["merchant_id"] == m) & (rels["entity_type"] == "ip") & (rels["end_time"] > conv_date)
        mask_dev = (rels["merchant_id"] == m) & (rels["entity_type"] == "device") & (rels["end_time"] > conv_date)
        rels.loc[mask_ip, "end_time"] = conv_date
        rels.loc[mask_dev, "end_time"] = conv_date
        
        new_rels.append({"merchant_id": m, "entity_type": "ip", "entity_id": shared_ip, "start_time": conv_date, "end_time": end_ts})
        new_rels.append({"merchant_id": m, "entity_type": "device", "entity_id": shared_dev, "start_time": conv_date, "end_time": end_ts})
        logger.log(conv_date, m, "IP_ADDED", shared_ip)
        logger.log(conv_date, m, "DEVICE_ADDED", shared_dev)
        
    rels = pd.concat([rels, pd.DataFrame(new_rels)], ignore_index=True)
    return rels, tx

def _apply_behavioral_transition(members, tx, start_ts, end_ts, rng):
    # Structure remains normal.
    # But after day 40, refund rates skyrocket and volume shifts to nights.
    transition_date = start_ts + pd.Timedelta(days=40)
    
    for m in members:
        mask = (tx["merchant_id"] == m) & (tx["timestamp"] >= transition_date)
        idx = tx.index[mask].to_numpy()
        if len(idx) == 0: continue
        
        # 60% refund rate after transition
        refund_idx = rng.choice(idx, size=int(len(idx) * 0.60), replace=False)
        tx.loc[refund_idx, "status"] = "REFUNDED"
        
        # Shift times to night (00:00 to 05:00)
        night_offsets = pd.to_timedelta(rng.integers(0, 5*3600, size=len(idx)), unit="s")
        # Keep the same date, just change the time
        dates = tx.loc[idx, "timestamp"].dt.normalize()
        tx.loc[idx, "timestamp"] = dates + night_offsets
        
    return tx
