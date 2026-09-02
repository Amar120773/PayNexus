import json
import pandas as pd
from pathlib import Path
from src.inference.store import PointInTimeStore
from src.inference.scorer import InferenceEngine

def generate_golden_baseline():
    store = PointInTimeStore.get_instance()
    engine = InferenceEngine.get_instance()

    merchants = ["M00109", "M00115", "M00002", "M00492", "M00150"]
    timestamps = ["2026-03-31 00:00:00", "2026-03-15 00:00:00", "2026-03-01 00:00:00"]
    
    test_cases = [{"merchant_id": m, "ts": ts} for m in merchants for ts in timestamps]

    baseline = {}

    for case in test_cases:
        m_id = case["merchant_id"]
        ts = case["ts"]
        
        # Get data
        m_df, tx_df, rels_df = store.get_network_subgraph(m_id, ts)
        
        # Score
        res = engine.score_merchant(m_id, ts, m_df, tx_df, rels_df)
        
        key = f"{m_id}_{ts}"
        # Format results
        baseline[key] = {
            "merchant_id": m_id,
            "scoring_timestamp": ts,
            "subgraph_sizes": {
                "merchants": len(m_df),
                "transactions": len(tx_df),
                "relationships": len(rels_df)
            },
            "probability": res["probability"],
            "risk_band": res["risk_band"],
            "threshold": engine.threshold,
            "features": res["evidence_features"],
            "shap_values": res["shap_values"] if "shap_values" in res else None
        }

    out_path = Path("reports/neo4j_parity_baseline.json")
    out_path.parent.mkdir(exist_ok=True, parents=True)
    with open(out_path, "w") as f:
        json.dump(baseline, f, indent=4)
        
    print(f"Golden baseline saved to {out_path}")

if __name__ == "__main__":
    import os
    os.environ["DATA_BACKEND"] = "csv"
    generate_golden_baseline()
