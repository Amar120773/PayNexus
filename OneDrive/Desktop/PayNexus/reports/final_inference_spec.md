# MuleHunter V2 Final Inference Architecture

This document describes the production inference architecture for MuleHunter V2, designed for strictly point-in-time and zero-leakage evaluation.

## 1. Inference API

The inference API is located in `src.inference.scorer.InferenceEngine`.

### Core Capabilities:
- **`score_merchant`**: Evaluates a single merchant up to a specific `scoring_timestamp`.
- **`score_network`**: Evaluates a merchant and its 1-hop neighborhood based on the active graph at `scoring_timestamp`.
- **`find_first_detection`**: Sequentially evaluates a merchant across a timeline to find the exact point it crossed the model threshold.

### Artifacts:
The inference engine lazily loads serialized artifacts created during training:
- `artifacts/model.pkl`: The frozen V2 MuleHunter model (RandomForest).
- `artifacts/threshold.json`: The optimal threshold selected against the holdout validation set.
- `artifacts/model_metadata.json`: Feature specifications and training metadata.

## 2. Zero-Leakage Point-in-Time Guarantees

The architecture guarantees zero leakage through the following mechanisms:

### a) Temporal Graph Scoping
When scoring a merchant at `scoring_timestamp=T`:
1. The global graph `G(T)` is constructed exclusively using relationships where `start_time <= T`.
2. Active edge constraints ensure relationships that ended before the evaluation window (30-day lookback) are dropped.
3. Network features (e.g., degree, PageRank, shared IPs) are computed entirely from `G(T)`.

### b) Forward-Looking Metric Elimination
Evolution features explicitly reference backward-looking deltas (e.g., `volume_delta_t2_t3`, `network_growth_t2_t3`) constructed entirely from events `< T`.
The previous `start_date` parameter (which leaked the end of the simulation) was removed in favor of `scoring_timestamp_str`.

### c) Strict Label Omission
`network_id`, `is_mule`, and `mule_type` are explicitly banned from the inference pipeline and are scrubbed prior to any modeling.

### d) Threshold Enforcement
Thresholds are fixed at training time using a designated validation set, ensuring that operational classification boundaries are not retroactively fitted to the test period.

## 3. Usage Example

```python
from src.inference.scorer import score_merchant

# Safely evaluate a merchant exactly as they appeared on Jan 15th
result = score_merchant(
    merchant_id="M001",
    scoring_timestamp="2024-01-15 00:00:00",
    merchants=merchants_df,
    transactions=transactions_df,
    relationships=relationships_df
)

print(result["risk_band"]) # "HIGH", "MEDIUM", "LOW"
print(result["risk_score"]) # e.g. 84.5
```
