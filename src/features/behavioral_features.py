"""Behavioral feature extraction for merchants in MuleHunter."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


def extract_behavioral_features(
    dataset: Mapping[str, pd.DataFrame],
    merchants_df: pd.DataFrame | None = None,
    merchant_subset: list[str] | None = None,
) -> pd.DataFrame:
    """Extract individual merchant-level behavioral features from transaction history.

    These features strictly capture individual operational patterns without looking
    at graph relationships or ground-truth mule labels.
    """
    if merchants_df is None:
        merchants = dataset["merchants"].copy()
    else:
        merchants = merchants_df.copy()
        
    if merchant_subset is not None:
        merchants = merchants[merchants["merchant_id"].isin(merchant_subset)]

    features = pd.DataFrame({"merchant_id": merchants["merchant_id"]})

    # Merchant profile attributes
    if "merchant_age_days" in merchants.columns:
        features["merchant_age_days"] = merchants["merchant_age_days"].fillna(0).astype(float)
    else:
        features["merchant_age_days"] = 0.0

    if "kyc_status" in merchants.columns:
        features["kyc_verified"] = (merchants["kyc_status"] == "VERIFIED").astype(float)
        features["kyc_pending"] = (merchants["kyc_status"] == "PENDING").astype(float)
        features["kyc_limited"] = (merchants["kyc_status"] == "LIMITED").astype(float)
    else:
        features["kyc_verified"] = 1.0
        features["kyc_pending"] = 0.0
        features["kyc_limited"] = 0.0

    tx = dataset["transactions"].copy()
    if merchant_subset is not None:
        tx = tx[tx["merchant_id"].isin(merchant_subset)]
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    tx["date"] = tx["timestamp"].dt.date

    # 1. Volume & Amount aggregates
    tx_grouped = tx.groupby("merchant_id")
    vol_stats = tx_grouped.agg(
        transaction_count=("transaction_id", "count"),
        total_transaction_volume=("amount", "sum"),
        average_transaction_amount=("amount", "mean"),
        median_transaction_amount=("amount", "median"),
        transaction_amount_std=("amount", "std"),
        unique_customer_count=("customer_id", "nunique"),
        unique_device_count=("device_id", "nunique"),
        unique_ip_count=("ip_id", "nunique"),
        active_days_count=("date", "nunique"),
    ).reset_index()

    # Fill NaNs in standard deviation (for merchants with 1 or 0 txs)
    vol_stats["transaction_amount_std"] = vol_stats["transaction_amount_std"].fillna(0.0)

    features = features.merge(vol_stats, on="merchant_id", how="left").fillna(0.0)

    # 2. Success, Failure, and Refund rates
    status_counts = pd.crosstab(tx["merchant_id"], tx["status"], normalize="index").reset_index()
    for status_col in ["SUCCESS", "FAILED", "REFUNDED"]:
        if status_col not in status_counts.columns:
            status_counts[status_col] = 0.0

    status_counts = status_counts.rename(
        columns={
            "SUCCESS": "success_rate",
            "FAILED": "failure_rate",
            "REFUNDED": "refund_rate",
        }
    )
    features = features.merge(
        status_counts[["merchant_id", "success_rate", "failure_rate", "refund_rate"]],
        on="merchant_id",
        how="left",
    ).fillna(0.0)

    # 3. Refund aggregations
    refunds = dataset["refunds"].copy() if "refunds" in dataset else pd.DataFrame()
    if merchant_subset is not None and not refunds.empty and "merchant_id" in refunds.columns:
        refunds = refunds[refunds["merchant_id"].isin(merchant_subset)]
    if not refunds.empty and "merchant_id" in refunds.columns:
        refund_stats = refunds.groupby("merchant_id").agg(
            refund_count=("refund_id", "count"),
            refund_volume=("amount", "sum"),
        ).reset_index()
        features = features.merge(refund_stats, on="merchant_id", how="left").fillna(0.0)
    else:
        features["refund_count"] = 0.0
        features["refund_volume"] = 0.0

    features["refund_amount_ratio"] = np.where(
        features["total_transaction_volume"] > 0,
        features["refund_volume"] / features["total_transaction_volume"],
        0.0,
    )

    # 4. Settlement Accounts
    settlements = dataset["settlements"].copy() if "settlements" in dataset else pd.DataFrame()
    if merchant_subset is not None and not settlements.empty and "merchant_id" in settlements.columns:
        settlements = settlements[settlements["merchant_id"].isin(merchant_subset)]
    if not settlements.empty and "merchant_id" in settlements.columns:
        sa_stats = settlements.groupby("merchant_id").agg(
            unique_settlement_account_count=("settlement_account_id", "nunique"),
            settlement_count=("settlement_id", "count"),
            total_settlement_volume=("amount", "sum"),
        ).reset_index()
        features = features.merge(sa_stats, on="merchant_id", how="left").fillna(0.0)
    else:
        features["unique_settlement_account_count"] = 0.0
        features["settlement_count"] = 0.0
        features["total_settlement_volume"] = 0.0

    # 5. Payment method breakdown
    pm_counts = pd.crosstab(tx["merchant_id"], tx["payment_method"], normalize="index").reset_index()
    for method in ["UPI", "card", "netbanking", "wallet"]:
        col_name = f"pm_share_{method.lower()}"
        if method in pm_counts.columns:
            pm_counts = pm_counts.rename(columns={method: col_name})
        else:
            pm_counts[col_name] = 0.0
    features = features.merge(
        pm_counts[["merchant_id", "pm_share_upi", "pm_share_card", "pm_share_netbanking", "pm_share_wallet"]],
        on="merchant_id",
        how="left",
    ).fillna(0.0)

    # 6. Ratios & Velocities
    features["avg_tx_per_customer"] = np.where(
        features["unique_customer_count"] > 0,
        features["transaction_count"] / features["unique_customer_count"],
        0.0,
    )
    features["avg_tx_per_device"] = np.where(
        features["unique_device_count"] > 0,
        features["transaction_count"] / features["unique_device_count"],
        0.0,
    )
    features["avg_tx_per_ip"] = np.where(
        features["unique_ip_count"] > 0,
        features["transaction_count"] / features["unique_ip_count"],
        0.0,
    )
    features["transaction_velocity"] = np.where(
        features["active_days_count"] > 0,
        features["transaction_count"] / features["active_days_count"],
        0.0,
    )
    features["average_daily_volume"] = np.where(
        features["active_days_count"] > 0,
        features["total_transaction_volume"] / features["active_days_count"],
        0.0,
    )

    # 7. Volume Growth (Ratio of second-half volume vs first-half volume)
    if not tx.empty:
        min_date = tx["timestamp"].min()
        max_date = tx["timestamp"].max()
        mid_date = min_date + (max_date - min_date) / 2

        tx_first_half = tx[tx["timestamp"] < mid_date].groupby("merchant_id")["amount"].sum().rename("vol_h1")
        tx_second_half = tx[tx["timestamp"] >= mid_date].groupby("merchant_id")["amount"].sum().rename("vol_h2")
        halves = pd.concat([tx_first_half, tx_second_half], axis=1).fillna(0.0).reset_index()

        halves["volume_growth"] = np.where(
            halves["vol_h1"] > 0,
            (halves["vol_h2"] - halves["vol_h1"]) / halves["vol_h1"],
            np.where(halves["vol_h2"] > 0, 1.0, 0.0),
        )
        # Clip extreme outliers to reasonable numerical range
        halves["volume_growth"] = halves["volume_growth"].clip(lower=-1.0, upper=10.0)

        features = features.merge(halves[["merchant_id", "volume_growth"]], on="merchant_id", how="left").fillna(0.0)
    else:
        features["volume_growth"] = 0.0

    return features
