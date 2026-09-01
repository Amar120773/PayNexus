# MuleHunter V2 Inference Architecture Audit

## 1. Current Architecture
The current V2 pipeline is strictly designed for batch research and experimentation:
1. **Data Generation**: Creates synthetic evolving ecosystems with injected mules (`src/data_generation_v2/`).
2. **Feature Extraction**: Extracts features (`src/features_v2/evolution_features.py`) across the entire dataset using fixed 30/60/90-day forward windows from a global `start_date_str`.
3. **Model Evaluation**: Trains XGBoost models in a cross-validation loop (`src/evaluate_v2.py`) to compute ablation metrics, or trains a single train/val/test split (`src/models/mulehunter.py`).
4. **Discard**: Model weights and optimal thresholds are held in memory to generate predictions and metrics, then discarded.

## 2. Reusable Components
*   **Feature Math**: The underlying calculations in `extract_evolution_features` for `churn_rate` and `volume_delta`.
*   **Model configuration**: The XGBoost hyperparameters in `model_utils.py` and `evaluate_v2.py`.
*   **Threshold logic**: `find_optimal_threshold` from `model_utils.py`.

## 3. Components Requiring Refactoring
*   **`src/features_v2/evolution_features.py`**:
    *   **Temporal Logic**: Must shift from a global forward-looking `start_date` to a backward-looking `scoring_timestamp` (T=now, T-30, T-60).
    *   **Graph Construction**: The bipartite graph `nx.Graph()` is currently built only from the `valid_merchants` subset. If scoring a single merchant, this results in a graph of size 1 (zero shared peers). The graph must be built globally, then features extracted locally.
*   **Model Training**: A new script must be created to train on the full dataset (or train+val) and **serialize** the final model and threshold to disk for inference.

## 4. Leakage Risks
*   **Graph Structural Leakage**: To prevent label leakage during research, the pipeline filters relationships to `valid_merchants`. For inference, this breaks the network size calculation. Inference requires access to the *global* historical relationship graph.
*   **Temporal Leakage**: The current pipeline passes the entire `transactions` and `relationships` dataframes. For inference, strict filters must ensure no data > `scoring_timestamp` is accessible.
*   **Label Leakage**: `evaluate_v2.py` merges features with `merchant_labels.csv` during the pipeline. Inference must have zero dependency on label files.

## 5. Model Artifact Location
*   **Current**: None. The model is trained in memory and discarded.
*   **Required**: Needs a designated artifact path (e.g., `artifacts/model.pkl`).

## 6. Feature Artifact Location
*   **Current**: `data/synthetic_v2/evolution_features.csv`.
*   **Required**: For inference, features will likely be computed on-the-fly and passed in memory, or saved to a database table.

## 7. Threshold Artifact Location
*   **Current**: None. Kept in memory and printed to stdout.
*   **Required**: Needs a designated artifact path (e.g., `artifacts/threshold.json`).

## 8. Required New Modules
*   `src/models/train_and_save.py` (or similar): To serialize the model and threshold.
*   `src/inference/scorer.py`: To orchestrate data loading, feature extraction, and model prediction for a single merchant at a specific timestamp.

## 9. Proposed Inference Flow
1.  **Input**: `merchant_id`, `scoring_timestamp`.
2.  **Data Fetch**: Load transactions and relationships strictly <= `scoring_timestamp`.
3.  **Feature Extraction**: Run refactored `extract_evolution_features`, providing the *global* historical relationships but targeting the single `merchant_id`.
4.  **Model Load**: Load `model.pkl` and `threshold.json`.
5.  **Score**: Generate `mule_probability`, compare against threshold, and output `risk_score` + `predicted_label`.

## 10. Tests Required
*   **Serialization Test**: Ensure the loaded model predictions perfectly match the in-memory model.
*   **Single-Merchant Parity Test**: Ensure `extract_evolution_features(valid_merchants=[M])` perfectly matches the row for `M` in `extract_evolution_features(valid_merchants=ALL)`.
*   **Temporal Safety Test**: Ensure any transactions post-`scoring_timestamp` are strictly ignored by the feature extractor.

---

**READY FOR IMPLEMENTATION**
