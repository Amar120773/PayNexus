"""Temporal feature extraction and multi-merchant coordination scoring for MuleHunter."""

from __future__ import annotations

from typing import Mapping

import networkx as nx
import numpy as np
import pandas as pd

from src.graph.build_graph import build_projected_merchant_graph


def extract_temporal_features(
    dataset: Mapping[str, pd.DataFrame],
    projected_graph: nx.Graph | None = None,
    merchants_df: pd.DataFrame | None = None,
    merchant_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Extract temporal features including intra-merchant timing and network coordination.

    Temporal features capture:
    1. Intra-merchant concentration (night share, weekend share, hourly concentration, burst ratio)
    2. Inter-merchant statistical coordination (correlated volume bursts with network neighbors)
    """
    if merchants_df is None:
        merchants = dataset["merchants"].copy()
    else:
        merchants = merchants_df.copy()
        
    if merchant_subset is not None:
        merchants = merchants[merchants["merchant_id"].isin(merchant_subset)]

    features = pd.DataFrame({"merchant_id": merchants["merchant_id"]})

    tx = dataset["transactions"].copy()
    if merchant_subset is not None:
        tx = tx[tx["merchant_id"].isin(merchant_subset)]
        
    if tx.empty:
        # Return zeros if empty
        for col in [
            "transaction_time_concentration",
            "night_tx_share",
            "business_hours_tx_share",
            "evening_tx_share",
            "weekend_tx_share",
            "transaction_burst_score",
            "volume_spike_score",
            "daily_volume_cv",
            "active_days_ratio",
            "coordinated_activity_score",
        ]:
            features[col] = 0.0
        return features

    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx["date"] = tx["timestamp"].dt.date
    tx["hour"] = tx["timestamp"].dt.hour
    tx["dayofweek"] = tx["timestamp"].dt.dayofweek

    min_date = tx["date"].min()
    max_date = tx["date"].max()
    total_days = max(1, (max_date - min_date).days + 1)

    # 1. Hourly & Daily distributions per merchant
    hourly_shares = pd.crosstab(tx["merchant_id"], tx["hour"], normalize="index")
    # Concentration (Normalized Herfindahl index across 24 hours: (H - 1/24) / (1 - 1/24))
    hhi = (hourly_shares ** 2).sum(axis=1)
    norm_hhi = ((hhi - (1.0 / 24.0)) / (1.0 - (1.0 / 24.0))).clip(lower=0.0, upper=1.0)
    features["transaction_time_concentration"] = features["merchant_id"].map(norm_hhi).fillna(0.0)

    # Night (0-5), Business (9-18), Evening (18-24) shares
    tx["is_night"] = tx["hour"].between(0, 5)
    tx["is_business"] = tx["hour"].between(9, 18)
    tx["is_evening"] = tx["hour"].between(18, 23)
    tx["is_weekend"] = tx["dayofweek"] >= 5

    timing_agg = tx.groupby("merchant_id").agg(
        night_tx_share=("is_night", "mean"),
        business_hours_tx_share=("is_business", "mean"),
        evening_tx_share=("is_evening", "mean"),
        weekend_tx_share=("is_weekend", "mean"),
        active_days=("date", "nunique"),
    ).reset_index()

    timing_agg["active_days_ratio"] = (timing_agg["active_days"] / total_days).clip(upper=1.0)
    features = features.merge(
        timing_agg[["merchant_id", "night_tx_share", "business_hours_tx_share", "evening_tx_share", "weekend_tx_share", "active_days_ratio"]],
        on="merchant_id",
        how="left",
    ).fillna(0.0)

    # 2. Daily Spikes and Burst Scores
    daily_tx = tx.groupby(["merchant_id", "date"]).agg(
        daily_count=("transaction_id", "count"),
        daily_amount=("amount", "sum"),
    ).reset_index()

    burst_stats = daily_tx.groupby("merchant_id").agg(
        max_daily_count=("daily_count", "max"),
        mean_daily_count=("daily_count", "mean"),
        max_daily_amount=("daily_amount", "max"),
        mean_daily_amount=("daily_amount", "mean"),
        std_daily_amount=("daily_amount", "std"),
    ).reset_index()

    burst_scores = np.where(
        burst_stats["mean_daily_count"] > 0,
        burst_stats["max_daily_count"] / burst_stats["mean_daily_count"],
        1.0,
    )
    burst_stats["transaction_burst_score"] = np.clip(burst_scores, 0.0, 20.0)

    volume_spikes = np.where(
        burst_stats["mean_daily_amount"] > 0,
        burst_stats["max_daily_amount"] / burst_stats["mean_daily_amount"],
        1.0,
    )
    burst_stats["volume_spike_score"] = np.clip(volume_spikes, 0.0, 20.0)

    volume_cvs = np.where(
        burst_stats["mean_daily_amount"] > 0,
        burst_stats["std_daily_amount"].fillna(0.0) / burst_stats["mean_daily_amount"],
        0.0,
    )
    burst_stats["daily_volume_cv"] = np.clip(volume_cvs, 0.0, 10.0)

    features = features.merge(
        burst_stats[["merchant_id", "transaction_burst_score", "volume_spike_score", "daily_volume_cv"]],
        on="merchant_id",
        how="left",
    ).fillna(0.0)

    # 3. Inter-Merchant Coordinated Activity Score
    if projected_graph is None:
        graph = build_projected_merchant_graph(dataset, merchant_subset=merchant_subset)
    else:
        graph = projected_graph

    coord_scores = _compute_coordinated_activity_scores(tx, graph, merchants["merchant_id"].tolist())
    features["coordinated_activity_score"] = features["merchant_id"].map(coord_scores).fillna(0.0)

    return features


def _compute_coordinated_activity_scores(
    tx: pd.DataFrame,
    graph: nx.Graph,
    all_merchants: list[str],
) -> dict[str, float]:
    """Compute statistical temporal similarity between each merchant and its network neighbors.

    For each connected pair (m1, m2), computes cosine similarity of daily transaction volume.
    The score for merchant m is the maximum similarity with any connected neighbor.
    """
    if tx.empty or graph.number_of_edges() == 0:
        return {m: 0.0 for m in all_merchants}

    # Build daily volume series per merchant
    daily_matrix = tx.pivot_table(
        index="merchant_id",
        columns="date",
        values="amount",
        aggfunc="sum",
        fill_value=0.0,
    )

    # Normalize vectors for cosine similarity
    matrix_vals = daily_matrix.to_numpy()
    norms = np.linalg.norm(matrix_vals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_matrix = matrix_vals / norms
    norm_df = pd.DataFrame(normalized_matrix, index=daily_matrix.index)

    coord_scores: dict[str, float] = {m: 0.0 for m in all_merchants}

    for node in graph.nodes:
        if node not in norm_df.index:
            continue
        neighbors = [n for n in graph.neighbors(node) if n in norm_df.index]
        if not neighbors:
            continue

        node_vec = norm_df.loc[node].to_numpy()
        neighbor_vecs = norm_df.loc[neighbors].to_numpy()

        similarities = neighbor_vecs.dot(node_vec)
        max_sim = float(np.max(similarities)) if len(similarities) > 0 else 0.0
        coord_scores[node] = round(max(0.0, max_sim), 4)

    return coord_scores
