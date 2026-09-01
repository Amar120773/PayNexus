"""Generate the pre-computed blind-spot report and save to artifacts/."""

import pandas as pd
from pathlib import Path
from src.inference.scorer import InferenceEngine
from src.monitoring.blind_spot import BlindSpotAnalyzer

def main():
    engine = InferenceEngine.get_instance()
    features_df = pd.read_csv("data/synthetic_v2/evolution_features.csv")
    labels = pd.read_csv("data/synthetic_v2/merchant_labels.csv")
    networks = pd.read_csv("data/synthetic_v2/mule_networks.csv")
    merchants_path = Path("data/synthetic_v2/merchants.csv")
    merchants_df = pd.read_csv(merchants_path) if merchants_path.exists() else None

    analyzer = BlindSpotAnalyzer(
        engine=engine,
        labels=labels,
        networks=networks,
        features_df=features_df,
        merchants_df=merchants_df,
        scoring_timestamp="2026-04-01",
    )

    print("Running full blind-spot analysis...")
    report = analyzer.run_full_analysis()

    out_path = Path("artifacts/blind_spot_report.json")
    report.save(out_path)
    print(f"Report saved to {out_path}")

    # Summary
    print(f"\n--- Global Metrics ---")
    for k, v in report.global_metrics.items():
        print(f"  {k}: {v}")

    print(f"\n--- Baseline (Validation) Metrics ---")
    for k, v in report.baseline_metrics.items():
        print(f"  {k}: {v}")

    print(f"\n--- Recall Degradation ---")
    for k, v in report.recall_degradation.items():
        print(f"  {k}: {v}")

    print(f"\n--- Blind Spots Detected: {len(report.blind_spots)} ---")
    for bs in report.blind_spots:
        print(f"  [{bs['severity']}] {bs['type']}: {bs['description']}")

if __name__ == "__main__":
    main()
