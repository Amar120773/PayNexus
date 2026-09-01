# MuleHunter: Final Verified Metrics

> **DISCLAIMER**: All metrics in this document are derived from synthetic-data experiments. They do not represent real-world or production performance.

---

## 1. Dataset

| Metric | Value | Source |
| :--- | :--- | :--- |
| Total merchants | 5,000 | `data/synthetic_v2/merchant_labels.csv` |
| Mule merchants | 298 (5.96%) | `reports/phase6_blind_spot_architecture.md` |
| Mule networks | 62 | `reports/phase6_blind_spot_architecture.md` |
| Total transactions | 150,000 | `reports/network_evolution_dataset_report.md` |
| Simulation period | 90 days (2026-01-01 to 2026-04-01) | `reports/phase6_blind_spot_architecture.md` |
| Mule lifecycle types | 4 (Type A–D) | `data/synthetic_v2/mule_networks.csv` |
| Benign ecosystem types | 2 (Fast Growth, Seasonal Spike) | `reports/network_evolution_dataset_report.md` |

### Mule Type Distribution (Ground Truth)

| Type | Name | Count | Source |
| :--- | :--- | :--- | :--- |
| A | Rapid Formation | 79 | `reports/phase6_blind_spot_architecture.md` |
| B | Gradual Expansion | 75 | `reports/phase6_blind_spot_architecture.md` |
| C | Infrastructure Convergence | 67 | `reports/phase6_blind_spot_architecture.md` |
| D | Behavioral Transition | 77 | `reports/phase6_blind_spot_architecture.md` |

---

## 2. Held-Out Evaluation Methodology

- **Split strategy**: Network-level held-out isolation. Entire mule networks are assigned to a single split (train, validation, or test). No test-network merchants appear in training-time graphs.
- **Train split**: 3,499 merchants
- **Validation split**: 751 merchants
- **Test split**: 750 merchants
- **Source**: `artifacts/model_metadata.json`

> [!IMPORTANT]
> The V1 model initially achieved 100% recall due to **structural information leakage** — training-time graph features included connectivity from test-set nodes. This was identified, documented in `reports/leakage_remediation.md`, and fully remediated in V2 by transitioning to network-isolated temporal features.

---

## 3. Model Ablation Results (V2 — Post-Remediation)

All metrics computed on the held-out test set using the frozen model and frozen threshold.

| Model | Features | Precision | Recall | F1 | ROC-AUC | PR-AUC | FPR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. Behavioral Static Baseline** | 2 | 0.097 | 0.404 | 0.157 | 0.613 | 0.235 | 23.7% |
| **B. Behavioral Trajectory** | 4 | 0.122 | 0.310 | 0.175 | 0.601 | 0.221 | 14.3% |
| **C. Static Network** | 1 | 0.348 | 0.731 | 0.470 | 0.866 | 0.594 | 8.7% |
| **D. Network Evolution** | 6 | 0.711 | 0.741 | 0.724 | 0.873 | 0.766 | 1.9% |
| **E. Behavior + Network Evolution** | **10** | **0.782** | **0.865** | **0.821** | **0.974** | **0.904** | **1.5%** |

**Source**: `reports/v2_model_comparison.csv`

---

## 4. Key Performance Highlights

### Network / Syndicate Recall
- **Overall recall**: 86.5% (`reports/research_freeze.md`)
- **Network recall** (at least one member of each network detected): Documented per-type below

### Per-Mule-Type Performance

| Mule Type | Recall | Source |
| :--- | :--- | :--- |
| **Type B (Gradual Expansion)** | 97.4% | `reports/research_freeze.md` |
| **Type C (Infrastructure Convergence)** | 91.8% | `reports/research_freeze.md` |
| **Type A (Rapid Formation)** | ~86% (inferred from overall) | `reports/research_freeze.md` |
| **Type D (Behavioral Transition)** | **65.6%** | `reports/research_freeze.md` |

### False Positive Rate
- **Final FPR**: 1.5% (`reports/research_freeze.md`)
- **Improvement over static behavior baseline**: 23.7% → 1.5% (−93.7% relative reduction)
- **Improvement over static network**: 8.7% → 1.5% (−82.8% relative reduction)

---

## 5. Temporal Results

- **Detection lead time**: Minimum 60 days (two 30-day observation windows required)
- **Temporal safety**: Adversarially verified — injecting future transactions and relationships does not change historical scores
- **Source**: `reports/research_freeze.md`, `tests/test_phase8_temporal_safety.py`

---

## 6. Type-D Performance (Known Blind Spot)

Type-D (Behavioral Transition) mules are the documented weak point:
- **Recall**: 65.6%
- **Root cause**: These mules maintain stable infrastructure (no device/IP churn) and only shift transaction behavior gradually. The 30-day temporal window resets before the behavioral delta accumulates sufficient signal.
- **Mitigation**: The investigator dashboard provides manual network visualization so analysts can observe expanding connections that the automated score misses.
- **Source**: `reports/research_freeze.md`, `reports/phase6_blind_spot_architecture.md`

---

## 7. Leakage Remediation

| Scenario | Recall | F1 | FPR | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **V1 Leaked Model** | 100.0% | 0.071 | 68.9% | Graph features leaked test-set structure. **INVALID.** |
| **V1 Remediated Model** | 40.0% | 0.053 | 35.8% | Static behavioral + static network without leakage. |
| **V2 Evolution Model (Final)** | 86.5% | 0.821 | 1.5% | Temporal evolution features, network-isolated splits. |

**Source**: `reports/leakage_remediation.md`, `reports/v2_model_comparison.csv`

> [!CAUTION]
> The V1 leaked model results (100% recall) are historical artifacts. They are explicitly **invalid** and must never be cited as MuleHunter performance. Only V2 post-remediation results are valid.

---

## 8. Model Artifact Summary

| Artifact | Value | Source |
| :--- | :--- | :--- |
| Model type | LightGBM (XGBoost-compatible) | `artifacts/model.pkl` |
| Feature count | 10 | `artifacts/model_metadata.json` |
| Threshold | 0.3263 | `artifacts/model_metadata.json` |
| Training timestamp | 2026-08-27 | `artifacts/model_metadata.json` |
| Status | **FROZEN** | `reports/research_freeze.md` |
