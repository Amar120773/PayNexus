"""V2 Data Generation: Evolving Networks and Temporal Relationships."""

from __future__ import annotations
import numpy as np
import pandas as pd
from faker import Faker
from typing import Mapping

from src.data_generation_v2.config import SyntheticDataConfig, CATEGORIES, PAYMENT_METHODS
from src.data_generation_v2.events import get_event_logger

PAYMENT_PROFILES = {
    "ecommerce": [0.3, 0.4, 0.2, 0.1],
    "electronics": [0.2, 0.5, 0.25, 0.05],
    "fashion": [0.4, 0.35, 0.15, 0.1],
    "grocery": [0.6, 0.15, 0.1, 0.15],
    "restaurant": [0.5, 0.2, 0.1, 0.2],
    "travel": [0.1, 0.5, 0.3, 0.1],
    "SaaS": [0.05, 0.7, 0.2, 0.05],
    "education": [0.2, 0.4, 0.3, 0.1],
    "healthcare": [0.3, 0.4, 0.2, 0.1],
    "services": [0.4, 0.3, 0.2, 0.1],
}

def generate_dataset(config: SyntheticDataConfig) -> Mapping[str, pd.DataFrame]:
    rng = np.random.default_rng(config.seed)
    fake = Faker()
    Faker.seed(config.seed)
    
    merchants = _generate_merchants(config, rng, fake)
    customers = pd.DataFrame({"customer_id": _ids("C", config.customers)})
    devices = pd.DataFrame({"device_id": _ids("D", config.devices)})
    ips = pd.DataFrame({"ip_id": _ids("I", config.ips)})
    accounts = pd.DataFrame({"account_id": _ids("A", config.settlement_accounts)})
    
    # Generate temporal assignments including BENIGN_FAST_GROWTH, etc.
    relationships = _generate_temporal_relationships(config, merchants, devices, ips, rng)
    
    transactions = _generate_temporal_transactions(config, merchants, customers, relationships, rng)
    
    return {
        "merchants": merchants,
        "customers": customers,
        "devices": devices,
        "ips": ips,
        "settlement_accounts": accounts,
        "transactions": transactions,
        "relationships": relationships
    }

def _ids(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{i:05d}" for i in range(1, count + 1)]

def _generate_merchants(config: SyntheticDataConfig, rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date)
    end = start + pd.Timedelta(days=config.period_days)
    
    onboarding_dates = []
    logger = get_event_logger()
    for i in range(config.merchants):
        if rng.random() < 0.25: # 25% onboard dynamically during window
            offset = rng.integers(0, config.period_days - 5)
            ob_date = start + pd.Timedelta(days=offset)
        else:
            ob_date = start - pd.Timedelta(days=rng.integers(10, 300))
        onboarding_dates.append(ob_date)
            
    m_ids = _ids("M", config.merchants)
    for m_id, ob_date in zip(m_ids, onboarding_dates):
        if ob_date >= start:
            logger.log(ob_date, m_id, "MERCHANT_ONBOARDED")
            
    categories = rng.choice(CATEGORIES, size=config.merchants)
    kyc = rng.choice(["VERIFIED", "PENDING", "LIMITED"], size=config.merchants, p=[0.86, 0.08, 0.06])
    
    return pd.DataFrame({
        "merchant_id": m_ids,
        "merchant_name": [fake.company() for _ in range(config.merchants)],
        "category": categories,
        "onboarding_date": pd.Series(onboarding_dates),
        "kyc_status": kyc,
    })

def _generate_temporal_relationships(config: SyntheticDataConfig, merchants: pd.DataFrame, devices: pd.DataFrame, ips: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    start_ts = pd.Timestamp(config.start_date)
    end_ts = start_ts + pd.Timedelta(days=config.period_days)
    
    rows = []
    logger = get_event_logger()
    i_ids = ips["ip_id"].to_numpy()
    d_ids = devices["device_id"].to_numpy()
    
    # Core assignment logic with churn
    for _, row in merchants.iterrows():
        m_id = row["merchant_id"]
        active_start = max(start_ts, row["onboarding_date"])
        
        ip = rng.choice(i_ids)
        dev = rng.choice(d_ids)
        
        rows.append({"merchant_id": m_id, "entity_type": "ip", "entity_id": ip, "start_time": active_start, "end_time": end_ts})
        rows.append({"merchant_id": m_id, "entity_type": "device", "entity_id": dev, "start_time": active_start, "end_time": end_ts})
        
        # Natural device churn (30% probability)
        if rng.random() < 0.30:
            churn_offset = pd.Timedelta(days=rng.integers(5, max(6, (end_ts - active_start).days - 5)))
            churn_time = active_start + churn_offset
            if churn_time < end_ts:
                rows[-1]["end_time"] = churn_time
                new_dev = rng.choice(d_ids)
                rows.append({"merchant_id": m_id, "entity_type": "device", "entity_id": new_dev, "start_time": churn_time, "end_time": end_ts})
                logger.log(churn_time, m_id, "DEVICE_REMOVED", dev)
                logger.log(churn_time, m_id, "DEVICE_ADDED", new_dev)
                
    rels_df = pd.DataFrame(rows)
    
    # Inject BENIGN_FAST_GROWTH (e.g., dense platforms)
    # Pick 20 platforms. A platform is a shared IP that rapidly acquires many merchants around Day 30-50.
    platforms = rng.choice(i_ids, size=20, replace=False)
    for p_ip in platforms:
        p_start = start_ts + pd.Timedelta(days=rng.integers(20, 50))
        target_merchants = rng.choice(merchants["merchant_id"], size=rng.integers(10, 30), replace=False)
        for tm in target_merchants:
            # Drop old IP, switch to platform IP
            mask = (rels_df["merchant_id"] == tm) & (rels_df["entity_type"] == "ip") & (rels_df["end_time"] > p_start)
            rels_df.loc[mask, "end_time"] = p_start
            new_row = pd.DataFrame([{"merchant_id": tm, "entity_type": "ip", "entity_id": p_ip, "start_time": p_start, "end_time": end_ts}])
            rels_df = pd.concat([rels_df, new_row], ignore_index=True)
            logger.log(p_start, tm, "NETWORK_JOINED", p_ip)

    return rels_df

def _generate_temporal_transactions(config, merchants, customers, rels, rng):
    c_ids = customers["customer_id"].to_numpy()
    ip_rels = rels[rels["entity_type"] == "ip"]
    dev_rels = rels[rels["entity_type"] == "device"]
    
    weights = rng.lognormal(0, 1.2, size=config.merchants)
    tx_counts = np.random.multinomial(config.transactions, weights / weights.sum())
    
    start_ts = pd.Timestamp(config.start_date)
    end_ts = start_ts + pd.Timedelta(days=config.period_days)
    
    tx_rows = []
    idx = 1
    
    # Generate seasonal benign spikes
    spike_merchants = set(rng.choice(merchants["merchant_id"], size=200, replace=False))
    
    merch_list = merchants.to_dict('records')
    for m, count in zip(merch_list, tx_counts):
        if count == 0: continue
        m_id = m["merchant_id"]
        valid_start = max(start_ts, m["onboarding_date"])
        if valid_start >= end_ts: continue
        
        window_seconds = int((end_ts - valid_start).total_seconds())
        if window_seconds <= 0: continue
        
        # Normal uniform timestamp distribution
        offsets = rng.integers(0, window_seconds, size=count)
        
        # BENIGN_SEASONAL_SPIKE logic
        if m_id in spike_merchants:
            # Shift 50% of volume into a 3-day window
            spike_size = int(count * 0.5)
            spike_start_sec = rng.integers(0, window_seconds - 3*86400) if window_seconds > 3*86400 else 0
            offsets[:spike_size] = rng.integers(spike_start_sec, spike_start_sec + 3*86400, size=spike_size)
            
        timestamps = valid_start + pd.to_timedelta(offsets, unit="s")
        
        m_ips = ip_rels[ip_rels["merchant_id"] == m_id]
        m_devs = dev_rels[dev_rels["merchant_id"] == m_id]
        m_custs = rng.choice(c_ids, size=min(len(c_ids), max(5, count // 4)), replace=False)
        
        for t in timestamps:
            valid_ip = m_ips[(m_ips["start_time"] <= t) & (m_ips["end_time"] > t)]
            ip = valid_ip["entity_id"].iloc[0] if not valid_ip.empty else rng.choice(m_ips["entity_id"].to_numpy())
            
            valid_dev = m_devs[(m_devs["start_time"] <= t) & (m_devs["end_time"] > t)]
            dev = valid_dev["entity_id"].iloc[0] if not valid_dev.empty else rng.choice(m_devs["entity_id"].to_numpy())
            
            stat_rand = rng.random()
            status = "FAILED" if stat_rand < 0.02 else ("REFUNDED" if stat_rand < 0.07 else "SUCCESS")
            
            tx_rows.append({
                "transaction_id": f"T{idx:08d}",
                "merchant_id": m_id,
                "customer_id": rng.choice(m_custs),
                "timestamp": t,
                "amount": np.round(rng.lognormal(mean=np.log(80), sigma=0.8), 2),
                "payment_method": rng.choice(PAYMENT_METHODS, p=PAYMENT_PROFILES[m["category"]]),
                "device_id": dev,
                "ip_id": ip,
                "status": status
            })
            idx += 1
            
    df = pd.DataFrame(tx_rows)
    return df.sort_values("timestamp").reset_index(drop=True)
