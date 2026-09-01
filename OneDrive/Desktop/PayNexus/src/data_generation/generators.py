"""Synthetic dataset generation and validation for MuleHunter."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from faker import Faker

from src.data_generation.config import CATEGORIES, PAYMENT_METHODS, SyntheticDataConfig
from src.data_generation.mule_injection import inject_mule_networks


Dataset = dict[str, pd.DataFrame]

CATEGORY_AMOUNT_MEDIANS = {
    "ecommerce": 900,
    "electronics": 4_500,
    "fashion": 1_200,
    "grocery": 450,
    "restaurant": 700,
    "travel": 6_500,
    "SaaS": 2_200,
    "education": 3_800,
    "healthcare": 1_800,
    "services": 1_500,
}

PAYMENT_PROFILES = {
    "ecommerce": [0.44, 0.33, 0.10, 0.13],
    "electronics": [0.30, 0.46, 0.15, 0.09],
    "fashion": [0.42, 0.36, 0.08, 0.14],
    "grocery": [0.60, 0.20, 0.04, 0.16],
    "restaurant": [0.58, 0.19, 0.03, 0.20],
    "travel": [0.18, 0.55, 0.22, 0.05],
    "SaaS": [0.20, 0.56, 0.18, 0.06],
    "education": [0.34, 0.25, 0.32, 0.09],
    "healthcare": [0.35, 0.38, 0.19, 0.08],
    "services": [0.48, 0.28, 0.15, 0.09],
}


def generate_dataset(config: SyntheticDataConfig) -> Dataset:
    """Generate all MuleHunter synthetic CSV tables in memory."""

    config.validate()
    rng = np.random.default_rng(config.seed)
    fake = Faker("en_IN")
    fake.seed_instance(config.seed)

    merchants = _generate_merchants(config, rng, fake)
    customers = _generate_customers(config, rng)
    devices = _generate_devices(config, rng)
    ips = _generate_ips(config, rng)
    settlement_accounts = _generate_settlement_accounts(config, rng)

    merchant_account_map = _merchant_settlement_account_map(
        merchants["merchant_id"].to_numpy(),
        settlement_accounts["settlement_account_id"].to_numpy(),
        rng,
    )
    transactions = _generate_transactions(config, merchants, customers, devices, ips, rng)

    injected = inject_mule_networks(
        config=config,
        rng=rng,
        merchants=merchants,
        transactions=transactions,
        customer_ids=customers["customer_id"].to_numpy(),
        device_ids=devices["device_id"].to_numpy(),
        ip_ids=ips["ip_id"].to_numpy(),
        settlement_account_ids=settlement_accounts["settlement_account_id"].to_numpy(),
        merchant_settlement_accounts=merchant_account_map,
    )

    refunds = _generate_refunds(injected.transactions, rng)
    settlements = _generate_settlements(config, injected.transactions, injected.merchant_settlement_accounts, rng)

    dataset: Dataset = {
        "merchants": merchants,
        "customers": customers,
        "devices": devices,
        "ips": ips,
        "settlement_accounts": settlement_accounts,
        "transactions": injected.transactions,
        "settlements": settlements,
        "refunds": refunds,
        "merchant_labels": injected.merchant_labels,
        "mule_networks": injected.mule_networks,
    }
    assert_dataset_valid(dataset, config)
    return dataset


def write_dataset(dataset: Mapping[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in dataset.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")


def validate_dataset(dataset: Mapping[str, pd.DataFrame], config: SyntheticDataConfig | None = None) -> list[str]:
    errors: list[str] = []
    required_tables = {
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
    }
    missing = required_tables - set(dataset)
    if missing:
        errors.append(f"missing tables: {sorted(missing)}")
        return errors

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
        if key not in frame.columns:
            errors.append(f"{table} missing primary key {key}")
        elif frame[key].duplicated().any():
            errors.append(f"{table} has duplicate {key}")

    merchants = set(dataset["merchants"]["merchant_id"])
    customers = set(dataset["customers"]["customer_id"])
    devices = set(dataset["devices"]["device_id"])
    ips = set(dataset["ips"]["ip_id"])
    settlement_accounts = set(dataset["settlement_accounts"]["settlement_account_id"])
    transactions = set(dataset["transactions"]["transaction_id"])
    networks = set(dataset["mule_networks"]["network_id"])

    _check_subset(errors, "transaction merchant_id", dataset["transactions"]["merchant_id"], merchants)
    _check_subset(errors, "transaction customer_id", dataset["transactions"]["customer_id"], customers)
    _check_subset(errors, "transaction device_id", dataset["transactions"]["device_id"], devices)
    _check_subset(errors, "transaction ip_id", dataset["transactions"]["ip_id"], ips)
    _check_subset(errors, "settlement merchant_id", dataset["settlements"]["merchant_id"], merchants)
    _check_subset(
        errors,
        "settlement settlement_account_id",
        dataset["settlements"]["settlement_account_id"],
        settlement_accounts,
    )
    _check_subset(errors, "refund transaction_id", dataset["refunds"]["transaction_id"], transactions)
    _check_subset(errors, "refund merchant_id", dataset["refunds"]["merchant_id"], merchants)

    labels = dataset["merchant_labels"]
    if len(labels) != len(dataset["merchants"]):
        errors.append("merchant_labels must contain exactly one row per merchant")
    mule_labels = labels[labels["is_mule"] == 1]
    legit_labels = labels[labels["is_mule"] == 0]
    _check_subset(errors, "mule label network_id", mule_labels["network_id"], networks)
    if legit_labels["network_id"].fillna("").astype(str).str.len().gt(0).any():
        errors.append("legitimate merchants must not have a network_id")
    if legit_labels["mule_type"].fillna("").astype(str).str.len().gt(0).any():
        errors.append("legitimate merchants must not have a mule_type")
    if not set(labels["is_mule"]).issubset({0, 1}):
        errors.append("is_mule must only contain 0/1")

    for table, column in [
        ("merchants", "onboarding_date"),
        ("customers", "customer_since"),
        ("devices", "first_seen"),
        ("ips", "first_seen"),
        ("settlement_accounts", "created_date"),
        ("transactions", "timestamp"),
        ("settlements", "timestamp"),
        ("refunds", "timestamp"),
    ]:
        if column in dataset[table].columns:
            parsed = pd.to_datetime(dataset[table][column], errors="coerce")
            if parsed.isna().any():
                errors.append(f"{table}.{column} contains invalid timestamps")

    if (dataset["transactions"]["amount"] <= 0).any():
        errors.append("transaction amounts must be positive")
    if (dataset["settlements"]["amount"] <= 0).any():
        errors.append("settlement amounts must be positive")
    if len(dataset["refunds"]) > 0:
        if (dataset["refunds"]["amount"] <= 0).any():
            errors.append("refund amounts must be positive")
        tx_amounts = dataset["transactions"].set_index("transaction_id")["amount"]
        refund_amounts = dataset["refunds"].set_index("transaction_id")["amount"]
        aligned_tx = tx_amounts.loc[refund_amounts.index]
        if (refund_amounts.to_numpy() > aligned_tx.to_numpy() + 0.01).any():
            errors.append("refund amounts must not exceed transaction amounts")

    if config is not None:
        expected_counts = {
            "merchants": config.merchants,
            "transactions": config.transactions,
            "customers": config.customers,
            "devices": config.devices,
            "ips": config.ips,
            "settlement_accounts": config.settlement_accounts,
            "mule_networks": config.mule_networks,
        }
        for table, expected in expected_counts.items():
            actual = len(dataset[table])
            if actual != expected:
                errors.append(f"{table} count {actual} != configured {expected}")

    return errors


def assert_dataset_valid(dataset: Mapping[str, pd.DataFrame], config: SyntheticDataConfig | None = None) -> None:
    errors = validate_dataset(dataset, config)
    if errors:
        raise ValueError("Dataset validation failed:\n- " + "\n- ".join(errors))


def _generate_merchants(config: SyntheticDataConfig, rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date)
    end = start + pd.Timedelta(days=config.period_days)
    category_probs = np.array([0.16, 0.08, 0.10, 0.10, 0.13, 0.07, 0.08, 0.08, 0.08, 0.12])
    categories = rng.choice(CATEGORIES, size=config.merchants, p=category_probs)
    ages = rng.gamma(shape=2.2, scale=145, size=config.merchants).astype(int) + 15
    ages = np.clip(ages, 15, 1_200)
    onboarding_dates = end - pd.to_timedelta(ages, unit="D")
    kyc_status = rng.choice(["VERIFIED", "PENDING", "LIMITED"], size=config.merchants, p=[0.86, 0.08, 0.06])

    return pd.DataFrame(
        {
            "merchant_id": _ids("M", config.merchants),
            "merchant_name": [fake.company() for _ in range(config.merchants)],
            "category": categories,
            "onboarding_date": onboarding_dates.date.astype(str),
            "kyc_status": kyc_status,
            "merchant_age_days": ages,
        }
    )


def _generate_customers(config: SyntheticDataConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date) - pd.Timedelta(days=365)
    regions = rng.choice(
        ["north", "south", "east", "west", "central"],
        size=config.customers,
        p=[0.24, 0.24, 0.18, 0.22, 0.12],
    )
    customer_since = start + pd.to_timedelta(rng.integers(0, 365, size=config.customers), unit="D")
    return pd.DataFrame(
        {
            "customer_id": _ids("C", config.customers),
            "customer_since": customer_since.date.astype(str),
            "region": regions,
        }
    )


def _generate_devices(config: SyntheticDataConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date) - pd.Timedelta(days=90)
    return pd.DataFrame(
        {
            "device_id": _ids("D", config.devices),
            "device_type": rng.choice(["mobile", "desktop", "tablet", "pos"], size=config.devices, p=[0.58, 0.27, 0.05, 0.10]),
            "os": rng.choice(["Android", "iOS", "Windows", "macOS", "Linux", "POS"], size=config.devices, p=[0.42, 0.18, 0.22, 0.08, 0.04, 0.06]),
            "first_seen": (start + pd.to_timedelta(rng.integers(0, 120, size=config.devices), unit="D")).date.astype(str),
        }
    )


def _generate_ips(config: SyntheticDataConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date) - pd.Timedelta(days=120)
    return pd.DataFrame(
        {
            "ip_id": _ids("IP", config.ips),
            "ip_type": rng.choice(["residential", "office", "cloud", "vpn"], size=config.ips, p=[0.48, 0.27, 0.17, 0.08]),
            "region": rng.choice(["north", "south", "east", "west", "central"], size=config.ips),
            "first_seen": (start + pd.to_timedelta(rng.integers(0, 150, size=config.ips), unit="D")).date.astype(str),
        }
    )


def _generate_settlement_accounts(config: SyntheticDataConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date) - pd.Timedelta(days=600)
    return pd.DataFrame(
        {
            "settlement_account_id": _ids("SA", config.settlement_accounts),
            "bank_name": rng.choice(["HDFC", "ICICI", "SBI", "Axis", "Kotak", "YES"], size=config.settlement_accounts),
            "account_type": rng.choice(["current", "savings", "nodal"], size=config.settlement_accounts, p=[0.72, 0.24, 0.04]),
            "created_date": (start + pd.to_timedelta(rng.integers(0, 650, size=config.settlement_accounts), unit="D")).date.astype(str),
        }
    )


def _merchant_settlement_account_map(
    merchant_ids: np.ndarray,
    settlement_account_ids: np.ndarray,
    rng: np.random.Generator,
) -> pd.Series:
    account_map = pd.Series(
        rng.choice(settlement_account_ids, size=len(merchant_ids), replace=True),
        index=merchant_ids,
        name="settlement_account_id",
    )
    shared_group_count = max(2, len(merchant_ids) // 35)
    for _ in range(shared_group_count):
        group_size = int(rng.integers(2, 6))
        merchants = rng.choice(merchant_ids, size=min(group_size, len(merchant_ids)), replace=False)
        account_map.loc[merchants] = str(rng.choice(settlement_account_ids))
    return account_map


def _generate_transactions(
    config: SyntheticDataConfig,
    merchants: pd.DataFrame,
    customers: pd.DataFrame,
    devices: pd.DataFrame,
    ips: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    merchant_ids = merchants["merchant_id"].to_numpy()
    customer_ids = customers["customer_id"].to_numpy()
    device_ids = devices["device_id"].to_numpy()
    ip_ids = ips["ip_id"].to_numpy()

    merchant_weights = rng.lognormal(mean=0.0, sigma=1.05, size=len(merchant_ids))
    merchant_weights[rng.choice(len(merchant_ids), size=max(1, len(merchant_ids) // 25), replace=False)] *= rng.uniform(2.0, 4.5)
    merchant_probs = merchant_weights / merchant_weights.sum()

    merchant_meta = merchants.set_index("merchant_id")["category"].to_dict()
    merchant_customer_pools = _merchant_customer_pools(merchants, customer_ids, rng)
    merchant_device_pools = _merchant_entity_pools(merchant_ids, device_ids, rng, min_size=2, max_size=8, shared_fraction=0.07)
    merchant_ip_pools = _merchant_entity_pools(merchant_ids, ip_ids, rng, min_size=2, max_size=7, shared_fraction=0.10)
    refund_rates, failure_rates = _merchant_status_rates(merchant_ids, rng)
    seasonal_merchants = set(rng.choice(merchant_ids, size=max(1, len(merchant_ids) // 12), replace=False))
    seasonal_days = {merchant_id: int(rng.integers(8, config.period_days - 8)) for merchant_id in seasonal_merchants}

    rows: list[dict[str, object]] = []
    chosen_merchants = rng.choice(merchant_ids, size=config.transactions, p=merchant_probs)
    for index, merchant_id in enumerate(chosen_merchants, start=1):
        category = merchant_meta[str(merchant_id)]
        amount = _sample_amount(category, rng)
        status = _sample_status(str(merchant_id), refund_rates, failure_rates, rng)
        rows.append(
            {
                "transaction_id": f"T{index:08d}",
                "merchant_id": merchant_id,
                "customer_id": _sample_customer(str(merchant_id), merchant_customer_pools, customer_ids, rng),
                "timestamp": _sample_timestamp(
                    config,
                    category,
                    str(merchant_id),
                    seasonal_days,
                    seasonal_merchants,
                    rng,
                ),
                "amount": amount,
                "payment_method": str(rng.choice(PAYMENT_METHODS, p=PAYMENT_PROFILES[category])),
                "device_id": _sample_from_pool(str(merchant_id), merchant_device_pools, device_ids, rng, pool_probability=0.84),
                "ip_id": _sample_from_pool(str(merchant_id), merchant_ip_pools, ip_ids, rng, pool_probability=0.86),
                "status": status,
            }
        )
    return pd.DataFrame(rows).sort_values("transaction_id").reset_index(drop=True)


def _generate_refunds(transactions: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    refunded = transactions[transactions["status"] == "REFUNDED"].copy().reset_index(drop=True)
    rows: list[dict[str, object]] = []
    reasons = ["customer_request", "duplicate_payment", "merchant_cancelled", "quality_issue", "pricing_error"]
    for index, row in refunded.iterrows():
        tx_time = pd.Timestamp(row["timestamp"])
        refund_time = tx_time + pd.Timedelta(hours=int(rng.integers(2, 240)), minutes=int(rng.integers(0, 60)))
        rows.append(
            {
                "refund_id": f"R{index + 1:08d}",
                "transaction_id": row["transaction_id"],
                "merchant_id": row["merchant_id"],
                "amount": round(float(row["amount"]) * float(rng.uniform(0.35, 1.0)), 2),
                "timestamp": refund_time,
                "reason": str(rng.choice(reasons, p=[0.36, 0.11, 0.21, 0.24, 0.08])),
            }
        )
    return pd.DataFrame(rows, columns=["refund_id", "transaction_id", "merchant_id", "amount", "timestamp", "reason"])


def _generate_settlements(
    config: SyntheticDataConfig,
    transactions: pd.DataFrame,
    merchant_account_map: pd.Series,
    rng: np.random.Generator,
) -> pd.DataFrame:
    start = pd.Timestamp(config.start_date)
    tx = transactions[transactions["status"].isin(["SUCCESS", "REFUNDED"])].copy()
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx["settlement_window"] = ((tx["timestamp"] - start).dt.days // 3).clip(lower=0)

    rows: list[dict[str, object]] = []
    grouped = tx.groupby(["merchant_id", "settlement_window"], sort=True)["amount"].sum()
    for index, ((merchant_id, window), gross_amount) in enumerate(grouped.items(), start=1):
        if gross_amount <= 0:
            continue
        timestamp = start + pd.Timedelta(days=int(window) * 3 + 3, hours=int(rng.integers(4, 28)))
        rows.append(
            {
                "settlement_id": f"S{index:08d}",
                "merchant_id": merchant_id,
                "settlement_account_id": merchant_account_map.loc[merchant_id],
                "amount": round(float(gross_amount) * float(rng.uniform(0.945, 0.995)), 2),
                "timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows)


def _merchant_customer_pools(
    merchants: pd.DataFrame,
    customer_ids: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    category_pools = {
        category: rng.choice(customer_ids, size=max(10, int(len(customer_ids) * 0.22)), replace=False)
        for category in CATEGORIES
    }
    pools: dict[str, np.ndarray] = {}
    for row in merchants.itertuples(index=False):
        pool_size = int(rng.integers(25, min(130, len(customer_ids)) + 1))
        category_size = int(pool_size * rng.uniform(0.55, 0.78))
        category_pool = category_pools[row.category]
        selected_category = rng.choice(category_pool, size=min(category_size, len(category_pool)), replace=False)
        remaining = max(1, pool_size - len(selected_category))
        selected_global = rng.choice(customer_ids, size=min(remaining, len(customer_ids)), replace=False)
        pools[row.merchant_id] = np.unique(np.concatenate([selected_category, selected_global]))
    return pools


def _merchant_entity_pools(
    merchant_ids: np.ndarray,
    entity_ids: np.ndarray,
    rng: np.random.Generator,
    *,
    min_size: int,
    max_size: int,
    shared_fraction: float,
) -> dict[str, np.ndarray]:
    shared_count = max(3, int(len(entity_ids) * shared_fraction))
    shared_entities = rng.choice(entity_ids, size=shared_count, replace=False)
    
    # Create explicit benign clusters (e.g., Aggregators, Shared Offices)
    cluster_count = max(2, int(len(merchant_ids) * 0.05))
    benign_clusters = []
    for _ in range(cluster_count):
        cluster_size = int(rng.integers(2, min(6, len(shared_entities) + 1)))
        cluster_entities = rng.choice(shared_entities, size=cluster_size, replace=False)
        benign_clusters.append(cluster_entities)

    pools: dict[str, np.ndarray] = {}
    for merchant_id in merchant_ids:
        pool_size = int(rng.integers(min_size, max_size + 1))
        local = rng.choice(entity_ids, size=pool_size, replace=False)
        
        # 40% chance to be part of a tight benign cluster (Aggregator/Office)
        if rng.random() < 0.40:
            cluster_entities = benign_clusters[rng.choice(len(benign_clusters))]
            local = np.unique(np.concatenate([local, cluster_entities]))
        # 20% chance for random loose sharing
        elif rng.random() < 0.20:
            shared = rng.choice(shared_entities, size=int(rng.integers(1, min(4, shared_count) + 1)), replace=False)
            local = np.unique(np.concatenate([local, shared]))
            
        pools[str(merchant_id)] = local
    return pools


def _merchant_status_rates(
    merchant_ids: np.ndarray,
    rng: np.random.Generator,
) -> tuple[dict[str, float], dict[str, float]]:
    refund_rates: dict[str, float] = {}
    failure_rates: dict[str, float] = {}
    high_refund_merchants = set(rng.choice(merchant_ids, size=max(1, len(merchant_ids) // 16), replace=False))
    high_failure_merchants = set(rng.choice(merchant_ids, size=max(1, len(merchant_ids) // 18), replace=False))
    for merchant_id in merchant_ids:
        refund = float(rng.beta(2.0, 70.0) + 0.004)
        failure = float(rng.beta(2.5, 55.0) + 0.008)
        if merchant_id in high_refund_merchants:
            refund += float(rng.uniform(0.035, 0.095))
        if merchant_id in high_failure_merchants:
            failure += float(rng.uniform(0.035, 0.075))
        refund_rates[str(merchant_id)] = min(refund, 0.18)
        failure_rates[str(merchant_id)] = min(failure, 0.16)
    return refund_rates, failure_rates


def _sample_status(
    merchant_id: str,
    refund_rates: Mapping[str, float],
    failure_rates: Mapping[str, float],
    rng: np.random.Generator,
) -> str:
    refund = refund_rates[merchant_id]
    failure = failure_rates[merchant_id]
    success = max(0.70, 1.0 - refund - failure)
    return str(rng.choice(["SUCCESS", "FAILED", "REFUNDED"], p=[success, failure, refund]))


def _sample_amount(category: str, rng: np.random.Generator) -> float:
    median = CATEGORY_AMOUNT_MEDIANS[category]
    amount = rng.lognormal(mean=np.log(median), sigma=0.72)
    if rng.random() < 0.015:
        amount *= float(rng.uniform(2.5, 6.0))
    return round(float(np.clip(amount, 20, 250_000)), 2)


def _sample_customer(
    merchant_id: str,
    merchant_customer_pools: Mapping[str, np.ndarray],
    customer_ids: np.ndarray,
    rng: np.random.Generator,
) -> str:
    if rng.random() < 0.88:
        return str(rng.choice(merchant_customer_pools[merchant_id]))
    return str(rng.choice(customer_ids))


def _sample_from_pool(
    merchant_id: str,
    pools: Mapping[str, np.ndarray],
    entity_ids: np.ndarray,
    rng: np.random.Generator,
    *,
    pool_probability: float,
) -> str:
    if rng.random() < pool_probability:
        return str(rng.choice(pools[merchant_id]))
    return str(rng.choice(entity_ids))


def _sample_timestamp(
    config: SyntheticDataConfig,
    category: str,
    merchant_id: str,
    seasonal_days: Mapping[str, int],
    seasonal_merchants: set[str],
    rng: np.random.Generator,
) -> pd.Timestamp:
    start = pd.Timestamp(config.start_date)
    if merchant_id in seasonal_merchants and rng.random() < 0.30:
        day = int(np.clip(rng.normal(seasonal_days[merchant_id], 2.5), 0, config.period_days - 1))
    else:
        day = int(rng.integers(0, config.period_days))

    peak_hour = {
        "restaurant": 19,
        "grocery": 11,
        "travel": 21,
        "SaaS": 14,
        "education": 16,
    }.get(category, 15)
    hour = int(np.clip(rng.normal(peak_hour, 4.2), 0, 23))
    minute = int(rng.integers(0, 60))
    second = int(rng.integers(0, 60))
    return start + pd.Timedelta(days=day, hours=hour, minutes=minute, seconds=second)


def _check_subset(errors: list[str], field_name: str, values: pd.Series, allowed: set[object]) -> None:
    invalid = set(values.dropna()) - allowed
    if invalid:
        errors.append(f"{field_name} has {len(invalid)} invalid reference(s)")


def _ids(prefix: str, count: int) -> list[str]:
    width = max(4, len(str(count)))
    return [f"{prefix}{index:0{width}d}" for index in range(1, count + 1)]
