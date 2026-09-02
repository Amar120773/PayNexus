import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.features.build_features import build_master_feature_table
from src.graph.build_graph import load_graph_data

def test_no_structural_leakage():
    # Load synthetic data
    dataset = load_graph_data("data/synthetic")
    
    # Create an artificial split where M0001 to M0350 are train, and rest are test
    merchants = dataset["merchants"]["merchant_id"].unique()
    train_merchants = merchants[:350]
    val_merchants = merchants[350:425]
    test_merchants = merchants[425:]
    
    splits_df = pd.DataFrame([
        {"merchant_id": m, "split": "train"} for m in train_merchants
    ] + [
        {"merchant_id": m, "split": "val"} for m in val_merchants
    ] + [
        {"merchant_id": m, "split": "test"} for m in test_merchants
    ])
    
    # Run full feature extraction (which includes test data in the global dataset dictionary)
    features_full, _ = build_master_feature_table(dataset, splits_df, data_dir="data/synthetic")
    train_features_full = features_full[features_full["merchant_id"].isin(train_merchants)].sort_values("merchant_id").reset_index(drop=True)
    
    # Now, explicitly DELETE all test and val merchants and their transactions from the dataset
    restricted_dataset = {}
    for table_name, df in dataset.items():
        if "merchant_id" in df.columns:
            restricted_dataset[table_name] = df[df["merchant_id"].isin(train_merchants)].copy()
        else:
            restricted_dataset[table_name] = df.copy()
            
    # Re-run feature extraction on the restricted dataset
    # We still pass the same splits_df, but the underlying data for val/test is gone.
    features_restricted, _ = build_master_feature_table(restricted_dataset, splits_df, data_dir="data/synthetic")
    train_features_restricted = features_restricted[features_restricted["merchant_id"].isin(train_merchants)].sort_values("merchant_id").reset_index(drop=True)
    
    # Assert that training features are IDENTICAL in both scenarios
    # This proves that the presence of test/val transactions in the raw dataset
    # did not leak into the training features (like PageRank).
    
    # Drop any potential tiny float precision differences by rounding
    cols_to_check = [c for c in train_features_full.columns if c not in ["merchant_id"]]
    
    for col in cols_to_check:
        full_vals = train_features_full[col].fillna(0.0).to_numpy()
        restr_vals = train_features_restricted[col].fillna(0.0).to_numpy()
        
        # Check if arrays are close
        if np.issubdtype(full_vals.dtype, np.number):
            np.testing.assert_allclose(
                full_vals, 
                restr_vals, 
                rtol=1e-5, 
                atol=1e-5, 
                err_msg=f"Leakage detected in feature: {col}"
            )
        else:
            np.testing.assert_array_equal(
                full_vals, 
                restr_vals, 
                err_msg=f"Leakage detected in categorical feature: {col}"
            )

    print("Success: No structural leakage detected. Train features are robust to test-set presence.")
