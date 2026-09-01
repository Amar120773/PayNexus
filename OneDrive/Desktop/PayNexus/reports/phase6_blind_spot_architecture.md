# Phase 6: Blind-Spot Discovery — Proposed Architecture

## 1. Problem Statement

The frozen V2 MuleHunter model (serialized in `artifacts/model.pkl`) was trained and evaluated on a single synthetic dataset snapshot. Phase 4B and Phase 5 established point-in-time safety and inference serving, but the system currently has **no mechanism** to detect when the model's predictions degrade over time or fail on specific subpopulations of merchants.

A production fraud-detection system must be able to answer:

1. **Recall Degradation**: Is the model missing more mules today than it was at training time?
2. **False-Negative Concentration**: Are the missed mules clustered in a specific mule type or network topology?
3. **Segment-Specific Failure**: Does the model perform well overall but collapse on merchants in a particular category, volume tier, or mule scenario?
4. **Feature Drift**: Have the distributions of the input features shifted enough from training that the model's decision surface is no longer calibrated?

---

## 2. Inventory of Existing Data and Capabilities

### 2.1 Ground Truth (Labels)

| Source | File | Key Columns | Notes |
|---|---|---|---|
| Merchant labels | `data/synthetic_v2/merchant_labels.csv` | `merchant_id`, `is_mule`, `network_id`, `mule_type` | 5000 merchants, 298 mules across 62 networks |
| Network metadata | `data/synthetic_v2/mule_networks.csv` | `network_id`, `primary_mule_type`, `merchant_count` | 4 scenario types: TYPE_A through TYPE_D |

**Mule type distribution** (ground truth):
- `TYPE_A_RAPID_FORMATION`: 79 merchants
- `TYPE_D_BEHAVIORAL_TRANSITION`: 77 merchants
- `TYPE_B_GRADUAL_EXPANSION`: 75 merchants
- `TYPE_C_INFRASTRUCTURE_CONVERGENCE`: 67 merchants

### 2.2 Prediction Capabilities

| Component | Location | Interface | Output |
|---|---|---|---|
| `InferenceEngine.score_merchant()` | `src/inference/scorer.py` | `(merchant_id, scoring_timestamp, merchants, tx, rels)` | `{merchant_id, probability, risk_score, risk_band, evidence_features}` |
| `InferenceEngine.score_network()` | `src/inference/scorer.py` | Same | List of per-merchant results for the 1-hop neighborhood |
| `InferenceEngine.find_first_detection()` | `src/inference/scorer.py` | `(merchant_id, ..., candidate_timestamps)` | Earliest timestamp where probability ≥ threshold |
| API adapter | `src/api/app.py` | `POST /v1/score/merchant`, `POST /v1/score/network` | JSON `ScoreResult` / `NetworkScoreResult` |

### 2.3 Features

| Feature Set | Count | Source |
|---|---|---|
| Evolution features (model inputs) | 10 delta + 3 static = 13 total | `extract_evolution_features()` in `src/features_v2/evolution_features.py` |
| Model uses | 10 features | `volume_delta_t1_t2`, `volume_delta_t2_t3`, `refund_delta_t1_t2`, `refund_delta_t2_t3`, `network_growth_t1_t2`, `network_growth_t2_t3`, `device_churn_t1_t2`, `device_churn_t2_t3`, `ip_churn_t1_t2`, `ip_churn_t2_t3` |
| Frozen training features | `data/synthetic_v2/evolution_features.csv` | Pre-computed at `scoring_timestamp = start_date + 90 days` |

### 2.4 Timestamps

| Element | Value |
|---|---|
| Simulation start | `2026-01-01` |
| Simulation end | `2026-04-01` (90-day period) |
| Training scoring timestamp | `2026-04-01` (start + 90 days) |
| T1 window | Days 1–30 |
| T2 window | Days 31–60 |
| T3 window | Days 61–90 |

### 2.5 Segmentation Axes Available

The following segmentation dimensions are available in the existing data without any new feature engineering:

| Axis | Source | Values |
|---|---|---|
| **Mule type** | `merchant_labels.mule_type` | 4 scenario types + benign |
| **Network** | `merchant_labels.network_id` | 62 distinct network IDs |
| **Merchant category** | `merchants.category` (from generators) | 10 categories (ecommerce, electronics, etc.) |
| **Volume tier** | Derivable from `transactions.amount` | Quantile-based (low/medium/high) |
| **Network size** | `mule_networks.merchant_count` | 3–7 per network |

### 2.6 Model Metadata

| Artifact | Content |
|---|---|
| `artifacts/model.pkl` | Frozen XGBClassifier (100 trees, depth 4) |
| `artifacts/model_metadata.json` | Feature list, threshold (0.3263), train/val/test split sizes |
| `artifacts/threshold.json` | Optimal threshold (0.3263) |

### 2.7 Existing Evaluation Code (V1 — Not Point-in-Time Safe)

- `src/evaluation/evaluate.py`: V1 ablation study and report generation (uses V1 data split, not V2)
- `src/evaluation/error_analysis.py`: V1 false-positive analysis (reads V1 `data/processed/` files)
- `src/evaluate_v2.py`: V2 5-fold cross-validation ablation (does **not** use the frozen model or threshold)
- `src/models/model_utils.py`: Contains `evaluate_predictions()` which computes precision, recall, F1, ROC-AUC, PR-AUC, FPR, and confusion matrix

> [!IMPORTANT]
> None of the existing evaluation code runs through the frozen inference engine or respects the serialized threshold. They all train fresh models. The blind-spot detector must use the **frozen** model and **frozen** threshold exclusively.

---

## 3. Proposed Architecture

```
                     ┌──────────────────────────┐
                     │  PointInTimeStore (DAL)   │
                     └────────────┬─────────────┘
                                  │ data
                                  ▼
┌─────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  Ground Truth   │───▶│  BlindSpotAnalyzer   │◀───│  InferenceEngine     │
│  (labels CSV)   │    │  src/monitoring/      │    │  (frozen model)      │
└─────────────────┘    │  blind_spot.py        │    └──────────────────────┘
                       └──────────┬─────────────┘
                                  │
                       ┌──────────▼─────────────┐
                       │  BlindSpotReport        │
                       │  (structured dict/JSON)  │
                       └──────────┬─────────────┘
                                  │
                       ┌──────────▼─────────────┐
                       │  GET /v1/monitoring/    │
                       │  blind-spots            │
                       │  (FastAPI endpoint)     │
                       └─────────────────────────┘
```

### 3.1 New Module: `src/monitoring/blind_spot.py`

This is the core analysis engine. It consumes predictions from the **frozen** inference engine and compares them against ground truth.

**Class: `BlindSpotAnalyzer`**

```python
class BlindSpotAnalyzer:
    def __init__(
        self,
        engine: InferenceEngine,
        store: PointInTimeStore,
        labels: pd.DataFrame,        # merchant_labels
        networks: pd.DataFrame,       # mule_networks
        scoring_timestamp: str,
    ):
        ...

    def run_full_analysis(self) -> BlindSpotReport:
        """Score all merchants and compute all blind-spot metrics."""
        ...
```

#### Core Methods

| Method | Purpose | Input | Output |
|---|---|---|---|
| `_score_all_merchants()` | Score every merchant using the frozen engine at the fixed scoring timestamp | labels, store, engine | DataFrame with `{merchant_id, probability, risk_band, predicted_label}` |
| `compute_global_metrics()` | Compute overall precision, recall, F1, FPR using frozen threshold | scored DataFrame + labels | dict of global metrics |
| `compute_segment_metrics()` | Compute metrics per segment axis (mule_type, category, volume_tier) | scored DataFrame + labels + segment column | DataFrame of per-segment metrics |
| `detect_recall_degradation()` | Compare global recall against a baseline (training-time recall) | global metrics + baseline | dict with `{baseline_recall, current_recall, degraded: bool}` |
| `detect_fn_concentration()` | Analyze false negatives by segment to find concentrated failure | scored DataFrame + labels | DataFrame of FN counts and rates per segment |
| `detect_feature_drift()` | Compare current feature distributions to training-time distributions | training features, current features | Per-feature drift metrics (PSI or KS statistic) |

### 3.2 Data Structure: `BlindSpotReport`

A structured, serializable result containing all findings:

```python
@dataclass
class BlindSpotReport:
    scoring_timestamp: str
    global_metrics: dict              # {precision, recall, f1, fpr, fn_count, fp_count}
    recall_degradation: dict          # {baseline_recall, current_recall, delta, degraded}
    segment_metrics: pd.DataFrame     # rows = segments, cols = metric columns
    fn_concentration: pd.DataFrame    # where are false negatives clustered?
    feature_drift: pd.DataFrame       # per-feature PSI or KS statistic
    blind_spots: list[dict]           # synthesized list of detected blind spots
```

### 3.3 Metrics

#### 3.3.1 Recall Degradation

| Metric | Formula | Alert Condition |
|---|---|---|
| `current_recall` | TP / (TP + FN) at frozen threshold | — |
| `baseline_recall` | Recall from the training-time validation set (stored or recomputed) | — |
| `recall_delta` | `current_recall - baseline_recall` | `recall_delta < -0.05` |

#### 3.3.2 False-Negative Concentration

For each segment `s` (mule_type, category, volume_tier):

| Metric | Formula |
|---|---|
| `fn_count_s` | Number of actual mules in segment `s` that were not flagged |
| `fn_rate_s` | `fn_count_s / total_mules_in_s` |
| `fn_share_s` | `fn_count_s / total_fn` (what fraction of all FNs are in this segment?) |
| `concentration_flag` | `fn_share_s > 2 * (total_mules_in_s / total_mules)` — segment contributes disproportionately more FNs than its population share |

#### 3.3.3 Segment-Specific Model Failure

For each segment `s`:

| Metric | Formula | Alert Condition |
|---|---|---|
| `segment_recall_s` | TP_s / (TP_s + FN_s) | `segment_recall_s < global_recall - 0.15` |
| `segment_precision_s` | TP_s / (TP_s + FP_s) | — |
| `segment_f1_s` | Harmonic mean | — |
| `segment_fpr_s` | FP_s / (FP_s + TN_s) | — |

#### 3.3.4 Feature Drift

For each of the 10 model features:

| Metric | Method | Alert Condition |
|---|---|---|
| Population Stability Index (PSI) | Compare training feature distribution (binned) to current feature distribution | `PSI > 0.2` (significant drift) |
| Kolmogorov–Smirnov statistic | Two-sample KS test between training and current feature vectors | `p-value < 0.01` |

The **training-time feature distributions** can be derived from the frozen `data/synthetic_v2/evolution_features.csv` (which was computed at the same scoring timestamp used for training).

---

## 4. Segmentation Strategy

The analyzer will segment merchants along the following axes. Each axis is already derivable from existing data without new feature engineering:

### 4.1 By Mule Type (Primary)

Segment the 298 labeled mules by `mule_type`:
- `TYPE_A_RAPID_FORMATION`
- `TYPE_B_GRADUAL_EXPANSION`
- `TYPE_C_INFRASTRUCTURE_CONVERGENCE`
- `TYPE_D_BEHAVIORAL_TRANSITION`

This directly answers: *"Which attack pattern does the model fail to detect?"*

### 4.2 By Merchant Category

The `merchants` DataFrame from `generate_dataset()` contains a `category` column (10 possible values). However, this column is **not** currently stored in `data/synthetic_v2/`. Two options:

> [!IMPORTANT]
> **Design Decision Required**: The `category` column exists at generation time but is not persisted to the synthetic_v2 CSV. We can either:
> - **(A)** Re-derive it by re-running the generator with the same seed (deterministic), or
> - **(B)** Modify `run_pipeline_v2.py` to also save a `merchants.csv` with the category column.
>
> Option B is preferable since it creates a persistent data artifact. This is a minor pipeline change, not an inference change.

### 4.3 By Volume Tier

Quantile-based bucketing of `volume_static_t3` (from the feature vector) into LOW / MEDIUM / HIGH tiers. This can be computed at analysis time from the feature extraction output. No new data needed.

---

## 5. Files to Create and Modify

### New Files

| File | Purpose |
|---|---|
| `src/monitoring/__init__.py` | Package init |
| `src/monitoring/blind_spot.py` | Core `BlindSpotAnalyzer` class and `BlindSpotReport` dataclass |
| `tests/test_blind_spot.py` | Unit and integration tests for the analyzer |

### Modified Files

| File | Change | Risk |
|---|---|---|
| `src/api/app.py` | Add `GET /v1/monitoring/blind-spots` endpoint | Low — additive only |
| `src/api/schemas.py` | Add Pydantic response model for blind-spot report | Low — additive only |
| `src/run_pipeline_v2.py` | Save `merchants.csv` with category column (optional, for segment axis 4.2) | Low — additive only |

### Files NOT Modified

| File | Reason |
|---|---|
| `src/inference/scorer.py` | The analyzer calls the existing scorer as-is |
| `src/features_v2/evolution_features.py` | The analyzer uses existing feature extraction |
| `src/inference/store.py` | The analyzer uses existing store methods |
| All existing tests | The analyzer is purely additive |

---

## 6. Testing Strategy

### 6.1 Unit Tests (`tests/test_blind_spot.py`)

| Test | What It Proves |
|---|---|
| `test_global_metrics_computed_correctly` | Given known predictions and labels, verify precision/recall/F1 match expected values |
| `test_fn_concentration_detected` | Given a scenario where all FNs are in one mule_type, assert that segment is flagged |
| `test_no_false_alert_on_balanced_fn` | Given evenly distributed FNs, assert no segment is flagged as concentrated |
| `test_segment_failure_detected` | Given one segment with 0% recall, assert it is identified as a blind spot |
| `test_feature_drift_detected` | Given a shifted feature distribution, assert PSI > 0.2 triggers a drift alert |
| `test_feature_drift_not_triggered_on_identical` | Given identical distributions, assert no drift alert |
| `test_uses_frozen_threshold` | Assert the analyzer uses the serialized threshold from `artifacts/threshold.json`, not a recomputed one |

### 6.2 Integration Tests

| Test | What It Proves |
|---|---|
| `test_end_to_end_blind_spot_analysis` | Run the full analyzer on the real synthetic data, verify it produces a structurally valid `BlindSpotReport` |
| `test_blind_spot_api_endpoint` | Hit `GET /v1/monitoring/blind-spots` via `TestClient` and verify 200 + valid JSON |

---

## 7. Open Questions

1. **Baseline recall value**: Should the baseline recall come from the training-time validation set (recomputed using the frozen model on the val split), or should it be a hardcoded constant from the Phase 4B training run? Recomputing is more rigorous but requires reconstructing the val split.

2. **Merchant category persistence** (see Section 4.2): Do you want me to add `merchants.csv` to the pipeline output, or should I re-derive categories from the generator seed?

3. **Drift reference set**: Should the training-time feature distributions for PSI be computed from the full `evolution_features.csv` (all 5000 merchants) or only from the training split (3499 merchants)? Using only the training split is more statistically correct.

4. **API caching**: The blind-spot analysis requires scoring every merchant, which is computationally expensive. Should the API endpoint compute on-demand, or should we support a pre-computed cached report that is refreshed on a schedule?
