"""Network-level train/validation/test split for MuleHunter."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

import networkx as nx
import numpy as np
import pandas as pd

from src.graph.build_graph import build_projected_merchant_graph, load_graph_data


def generate_network_splits(
    labels_df: pd.DataFrame,
    merchants_df: pd.DataFrame,
    projected_graph: nx.Graph | None = None,
    seed: int = 42,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> pd.DataFrame:
    """Perform network-level splitting to prevent mule network leakage across sets.

    Splits entire mule networks (and their members) atomically into train/val/test.
    Legitimate merchants connected to validation or test mule networks are routed
    to validation/test respectively to eliminate indirect graph contamination.
    Remaining legitimate merchants are distributed according to the target split ratios.
    """
    rng = np.random.default_rng(seed)

    labels = labels_df.copy()
    labels["network_id"] = labels["network_id"].fillna("").astype(str)
    labels["is_mule"] = labels["is_mule"].fillna(0).astype(int)

    # 1. Identify mule networks
    mule_rows = labels[labels["is_mule"] == 1]
    unique_networks = sorted([net for net in mule_rows["network_id"].unique() if net])
    rng.shuffle(unique_networks)

    n_networks = len(unique_networks)
    n_train_nets = max(1, int(round(n_networks * train_ratio)))
    n_val_nets = max(1, int(round(n_networks * val_ratio)))
    # Ensure at least 1 test network if n_networks >= 3
    if n_train_nets + n_val_nets >= n_networks and n_networks >= 3:
        n_train_nets = n_networks - 2
        n_val_nets = 1
    n_test_nets = n_networks - n_train_nets - n_val_nets
    if n_test_nets <= 0 and n_networks >= 3:
        n_test_nets = 1
        n_train_nets -= 1

    train_networks = set(unique_networks[:n_train_nets])
    val_networks = set(unique_networks[n_train_nets : n_train_nets + n_val_nets])
    test_networks = set(unique_networks[n_train_nets + n_val_nets :])

    splits: dict[str, str] = {}

    # Assign all mule merchants according to their network
    for _, row in mule_rows.iterrows():
        net = row["network_id"]
        if net in train_networks:
            splits[row["merchant_id"]] = "train"
        elif net in val_networks:
            splits[row["merchant_id"]] = "val"
        elif net in test_networks:
            splits[row["merchant_id"]] = "test"
        else:
            splits[row["merchant_id"]] = "train"

    # 2. Identify legitimate merchants with strong infrastructure/settlement links to holdout networks
    legit_merchants = labels[labels["is_mule"] == 0]["merchant_id"].tolist()
    
    val_mules = set(mule_rows[mule_rows["network_id"].isin(val_networks)]["merchant_id"])
    test_mules = set(mule_rows[mule_rows["network_id"].isin(test_networks)]["merchant_id"])

    val_legit_strong_links = set()
    test_legit_strong_links = set()

    if projected_graph is not None:
        for m in legit_merchants:
            if projected_graph.has_node(m):
                for neighbor in projected_graph.neighbors(m):
                    edge_data = projected_graph[m][neighbor]
                    has_strong_link = (
                        edge_data.get("shared_settlements", 0) > 0
                        or edge_data.get("shared_devices", 0) > 0
                        or edge_data.get("shared_ips", 0) > 0
                    )
                    if has_strong_link:
                        if neighbor in test_mules:
                            test_legit_strong_links.add(m)
                        elif neighbor in val_mules:
                            val_legit_strong_links.add(m)

    # Route strongly-linked legitimate merchants to val/test
    for m in test_legit_strong_links:
        splits[m] = "test"
    for m in val_legit_strong_links:
        if m not in splits:
            splits[m] = "val"

    # 3. Distribute remaining independent legitimate merchants to match target 70/15/15 balance
    unassigned_legit = [m for m in legit_merchants if m not in splits]
    rng.shuffle(unassigned_legit)

    total_merchants = len(merchants_df)
    target_total_train = int(round(total_merchants * train_ratio))
    target_total_val = int(round(total_merchants * val_ratio))

    current_train = sum(1 for s in splits.values() if s == "train")
    current_val = sum(1 for s in splits.values() if s == "val")

    needed_train = max(0, target_total_train - current_train)
    needed_val = max(0, target_total_val - current_val)

    train_legit = unassigned_legit[:needed_train]
    val_legit = unassigned_legit[needed_train : needed_train + needed_val]
    test_legit = unassigned_legit[needed_train + needed_val :]

    for m in train_legit:
        splits[m] = "train"
    for m in val_legit:
        splits[m] = "val"
    for m in test_legit:
        splits[m] = "test"

    # Ensure all merchants in merchants_df are accounted for
    all_merchants = merchants_df["merchant_id"].tolist()
    for m in all_merchants:
        if m not in splits:
            splits[m] = "train"

    split_df = pd.DataFrame(
        [{"merchant_id": m, "split": splits[m]} for m in all_merchants]
    ).sort_values("merchant_id").reset_index(drop=True)

    return split_df


def save_splits(split_df: pd.DataFrame, output_path: Path | str = "data/processed/splits.csv") -> None:
    """Save merchant split assignments to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    split_df.to_csv(path, index=False)


def main() -> None:
    """Generate and save network-level splits."""
    parser = argparse.ArgumentParser(description="Create network-level train/val/test splits.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--output-file", type=Path, default=Path("data/processed/splits.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("Generating network-level held-out train/validation/test splits...")
    labels_df = pd.read_csv(args.data_dir / "merchant_labels.csv")
    merchants_df = pd.read_csv(args.data_dir / "merchants.csv")
    dataset = load_graph_data(args.data_dir)
    projected_graph = build_projected_merchant_graph(dataset)

    split_df = generate_network_splits(
        labels_df=labels_df,
        merchants_df=merchants_df,
        projected_graph=projected_graph,
        seed=args.seed,
    )
    save_splits(split_df, args.output_file)

    counts = split_df["split"].value_counts().to_dict()
    print(f"Splits saved to {args.output_file}")
    print(f"Split distribution: {counts}")


if __name__ == "__main__":
    main()
