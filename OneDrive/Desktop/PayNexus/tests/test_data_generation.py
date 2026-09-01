from __future__ import annotations

import pandas as pd

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import assert_dataset_valid, generate_dataset, validate_dataset, write_dataset


def small_config(seed: int = 123) -> SyntheticDataConfig:
    return SyntheticDataConfig(
        merchants=80,
        transactions=1_200,
        customers=220,
        devices=120,
        ips=130,
        settlement_accounts=125,
        mule_networks=4,
        period_days=75,
        seed=seed,
    )


def test_dataset_generation_counts_and_core_tables() -> None:
    dataset = generate_dataset(small_config())

    assert len(dataset["merchants"]) == 80
    assert len(dataset["transactions"]) == 1_200
    assert len(dataset["customers"]) == 220
    assert len(dataset["devices"]) == 120
    assert len(dataset["ips"]) == 130
    assert len(dataset["settlement_accounts"]) == 125
    assert len(dataset["mule_networks"]) == 4
    assert set(dataset) == {
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


def test_schema_validation_and_referential_integrity() -> None:
    config = small_config()
    dataset = generate_dataset(config)

    assert validate_dataset(dataset, config) == []
    assert_dataset_valid(dataset, config)


def test_reproducibility_with_same_seed() -> None:
    config = small_config(seed=777)
    first = generate_dataset(config)
    second = generate_dataset(config)

    for table in first:
        pd.testing.assert_frame_equal(first[table], second[table])


def test_different_seed_changes_transactions() -> None:
    first = generate_dataset(small_config(seed=111))
    second = generate_dataset(small_config(seed=222))

    assert not first["transactions"].equals(second["transactions"])


def test_mule_network_injection_labels_and_patterns() -> None:
    dataset = generate_dataset(small_config())
    labels = dataset["merchant_labels"]
    mule_labels = labels[labels["is_mule"] == 1]

    assert len(mule_labels) >= 4
    assert mule_labels["network_id"].nunique() == 4
    assert mule_labels["mule_type"].isin(
        ["ABNORMAL_VOLUME_SPIKE", "ABNORMAL_REFUND_RATE", "ABNORMAL_FAILURE_RATE", "ABNORMAL_TICKET_SIZE"]
    ).all()
    assert (dataset["mule_networks"]["merchant_count"].between(1, 3)).all()


def test_ground_truth_not_leaked_into_operational_tables() -> None:
    dataset = generate_dataset(small_config())
    forbidden = {"is_mule", "mule_type", "network_id"}

    for table in ["merchants", "customers", "devices", "ips", "settlement_accounts", "transactions", "settlements", "refunds"]:
        assert forbidden.isdisjoint(dataset[table].columns)


def test_writer_creates_csv_files(tmp_path) -> None:
    config = small_config()
    dataset = generate_dataset(config)
    write_dataset(dataset, tmp_path)

    for table in dataset:
        assert (tmp_path / f"{table}.csv").exists()
