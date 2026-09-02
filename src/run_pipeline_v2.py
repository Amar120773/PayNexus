"""V2 Pipeline: Temporal Dataset Generation and Descriptive Analysis."""

from __future__ import annotations
import os
import pandas as pd
from pathlib import Path
from src.data_generation_v2.config import SyntheticDataConfig
from src.data_generation_v2.generators import generate_dataset
from src.data_generation_v2.mule_injection import inject_mule_networks
from src.data_generation_v2.events import get_event_logger
from src.features_v2.evolution_features import extract_evolution_features
import numpy as np

def run_v2_pipeline() -> None:
    config = SyntheticDataConfig()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    
    print(f"==================================================")
    print(f"STEP 1: Generating Dataset V2")
    print(f"==================================================")
    
    rng = np.random.default_rng(config.seed)
    
    # 1. Base generation
    print("Generating base evolving ecosystem...")
    raw_dataset = generate_dataset(config)
    
    # 2. Mule injection
    print("Injecting temporal mule lifecycles...")
    result = inject_mule_networks(
        config=config,
        rng=rng,
        merchants=raw_dataset["merchants"],
        transactions=raw_dataset["transactions"],
        relationships=raw_dataset["relationships"]
    )
    
    # Save outputs
    print(f"Saving artifacts to {config.output_dir}...")
    raw_dataset["merchants"].to_csv(config.output_dir / "merchants.csv", index=False)
    result.transactions.to_csv(config.output_dir / "transactions.csv", index=False)
    result.merchant_labels.to_csv(config.output_dir / "merchant_labels.csv", index=False)
    result.mule_networks.to_csv(config.output_dir / "mule_networks.csv", index=False)
    result.relationships.to_csv(config.output_dir / "relationships.csv", index=False)
    
    logger = get_event_logger()
    events_df = logger.to_dataframe()
    events_df.to_csv(config.output_dir / "events.csv", index=False)
    
    print(f"Generated {len(events_df)} temporal lifecycle events.")
    print(f"Generated {len(result.transactions)} transactions.")
    
    print(f"==================================================")
    print(f"STEP 2: Trajectory Feature Extraction")
    print(f"==================================================")
    features = extract_evolution_features(
        merchants=raw_dataset["merchants"],
        transactions=result.transactions,
        relationships=result.relationships,
        scoring_timestamp_str=str(pd.Timestamp(config.start_date) + pd.Timedelta(days=90))
    )
    features.to_csv(config.output_dir / "evolution_features.csv", index=False)
    
    print(f"==================================================")
    print(f"STEP 3: Descriptive Analysis")
    print(f"==================================================")
    # Join features with labels to analyze the difference between Mules and Benign networks
    analysis_df = features.merge(result.merchant_labels[["merchant_id", "is_mule"]], on="merchant_id")
    
    numeric_cols = analysis_df.select_dtypes(include=np.number).columns.tolist()
    if "is_mule" not in numeric_cols:
        numeric_cols.append("is_mule")
    desc = analysis_df[numeric_cols].groupby("is_mule").mean().T
    desc.to_csv("reports/network_evolution_descriptive_analysis.csv")
    print("Descriptive analysis saved to reports/network_evolution_descriptive_analysis.csv")
    
    print("V2 Dataset generation and descriptive analysis complete!")
    print("Inspect reports/network_evolution_descriptive_analysis.csv to determine if a signal exists.")

if __name__ == "__main__":
    run_v2_pipeline()
