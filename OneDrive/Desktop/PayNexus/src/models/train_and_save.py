"""Train and serialize the frozen V2 MuleHunter model."""

import json
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.models.model_utils import create_classifier, find_optimal_threshold

def main():
    features_path = Path("data/synthetic_v2/evolution_features.csv")
    labels_path = Path("data/synthetic_v2/merchant_labels.csv")
    
    if not features_path.exists() or not labels_path.exists():
        print("Data missing. Please run src/run_pipeline_v2.py first.")
        return
        
    features_df = pd.read_csv(features_path)
    labels_df = pd.read_csv(labels_path)
    
    # Merge and align
    merged = features_df.merge(labels_df[["merchant_id", "is_mule"]], on="merchant_id")
    
    # Approved MVP features based on freeze document
    feature_cols = [
        "volume_delta_t1_t2", "volume_delta_t2_t3",
        "refund_delta_t1_t2", "refund_delta_t2_t3",
        "network_growth_t1_t2", "network_growth_t2_t3",
        "device_churn_t1_t2", "device_churn_t2_t3",
        "ip_churn_t1_t2", "ip_churn_t2_t3"
    ]
    
    X = merged[feature_cols].fillna(0).to_numpy()
    y = merged["is_mule"].to_numpy()
    
    # Train/Val/Test Split (70/15/15)
    # Strictly isolate the holdout set
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    
    # Split train_val into train and val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val
    )  # 0.1765 of 85% is ~15%
    
    print(f"Training on {len(X_train)} samples, validating on {len(X_val)}, testing on {len(X_test)}")
    
    # Train Frozen Model
    model = create_classifier(seed=42)
    model.fit(X_train, y_train)
    
    # Optimize Threshold on Validation Set
    val_probs = model.predict_proba(X_val)[:, 1]
    optimal_threshold = find_optimal_threshold(y_val, val_probs)
    print(f"Optimal Threshold on Validation Data: {optimal_threshold:.4f}")
    
    # Create Artifacts Directory
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    # Serialize Model
    model_path = artifacts_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    # Serialize Threshold
    threshold_path = artifacts_dir / "threshold.json"
    with open(threshold_path, "w") as f:
        json.dump({"optimal_threshold": float(optimal_threshold)}, f)
        
    # Metadata
    metadata = {
        "model_version": "v2_evolution",
        "feature_version": "1.0",
        "training_dataset_version": "v2",
        "random_seed": 42,
        "training_split": len(X_train),
        "validation_split": len(X_val),
        "test_split": len(X_test),
        "feature_list": feature_cols,
        "threshold": float(optimal_threshold),
        "training_timestamp": datetime.utcnow().isoformat()
    }
    
    metadata_path = artifacts_dir / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Artifacts successfully serialized to {artifacts_dir}/")

if __name__ == "__main__":
    main()
