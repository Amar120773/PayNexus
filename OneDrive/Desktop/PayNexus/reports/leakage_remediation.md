# MuleHunter: Leakage Remediation & Post-Analysis Report

## 1. The Leakage Mechanism
During our initial evaluation, the Full MuleHunter model (Behavior + Network + Temporal features) achieved an impossible **100% recall** and an inflated F1 score. A rigorous diagnostic pass revealed **structural information leakage**:

- **The Flaw:** In `src/graph/build_graph.py`, the network topological features (such as `pagerank_score`, `merchant_degree`, `betweenness_centrality`, and `connected_merchant_count`) were calculated over the **entire projected merchant graph** *before* the dataset was split into train, validation, and test sets.
- **The Leak:** While ground-truth `is_mule` labels were not explicitly leaked, the presence of test nodes and edges in the graph fundamentally altered the structural metrics for training nodes. The training data effectively used "future" test-set connectivity to shape its topological features, giving the model an artificial shortcut to detect mules.

## 2. Remediation Methodology
To remediate this, we transitioned from a **Global Graph** architecture to a **Simulated Batch Progression** architecture:
1. **Subgraph Projection:** Updated `build_projected_merchant_graph` and `build_heterogeneous_graph` to accept a `merchant_subset` parameter.
2. **Split-Specific Feature Extraction:** Refactored `build_master_feature_table` in `src/features/build_features.py` to iterate over the dataset splits:
   - **Train features** are calculated using *only* transactions, refunds, and settlements belonging to the train split.
   - **Validation features** use train + validation data.
   - **Test features** use all data (simulating production inference).
3. **Strict Data Filtering:** Updated `behavioral_features.py` and `temporal_features.py` to aggressively filter all underlying transaction data by `merchant_subset` before computing any timing or volume metrics, ensuring that global constants (e.g., dataset `max_date`) do not leak information into earlier splits.
4. **Leakage Audit:** Added `tests/test_leakage.py` which explicitly drops all test/val transactions from the dataset and asserts that the resulting training features are identical down to the floating-point level.

## 3. Before/After Metrics Comparison

| Model / Scenario | Precision | Recall | F1 Score | ROC-AUC | FPR |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Behavior Only)** | 0.0294 | 0.4000 | 0.0548 | 0.6095 | 34.74% |
| **Leaked MuleHunter** | 0.0368 | 1.0000 | 0.0709 | N/A | 68.95% |
| **Remediated MuleHunter** | 0.0286 | 0.4000 | 0.0533 | 0.6316 | 35.79% |

> [!IMPORTANT]
> **VERDICT:** The model performance now reflects reality. Without the structural leakage, the Full MuleHunter model performs similarly to the Baseline model (F1 ~0.0533 vs 0.0548). The impossible 100% recall has disappeared.

## 4. False Positive Analysis (Post-Remediation)
With the leakage removed, the model still exhibits a high False Positive Rate (~35%). Why?

We implemented and analyzed contextual network features: `ip_sharing_concentration`, `device_sharing_concentration`, and `customer_sharing_concentration`.

**Feature Distributions (Train Set):**
| Feature | Mule Mean | Legit Mean |
| --- | --- | --- |
| ip_sharing_concentration | 0.63 | 0.65 |
| device_sharing_concentration | 0.67 | 0.64 |
| customer_sharing_concentration | 0.72 | 0.66 |

**Analysis of Top 30 False Positives:**
Legitimate merchants flagged as mules possess extremely high network degrees (`weighted_network_degree` > 500) and near **100% infrastructure sharing concentration** (e.g., `ip_sharing_concentration` ~ 1.00). 

**Conclusion:**
Concentration of shared infrastructure is **not unique to malicious mules**. Legitimate merchants share significant portions of their infrastructure (via common payment gateways, platforms, or aggregators), which entangles them in the graph. The current graph topology metrics (PageRank, degree) merely capture the *size* and *density* of these legitimate clusters, leading the model to falsely flag them as coordinated mule rings. Future iterations must differentiate between benign infrastructural sharing and malicious behavioral coordination.
