# PHASE X: SHAP EXPLAINABILITY — ARCHITECTURE AUDIT

## 1. Current Model Architecture & State
* **Model Type:** XGBoost Classifier (`xgboost` is installed, pipeline uses `create_classifier` which wraps XGBoost).
* **Artifact Locations:** `artifacts/model.pkl` (pickled model) and `artifacts/model_metadata.json` (frozen metadata including the optimal threshold and feature ordering).
* **Model State:** FROZEN. The threshold is strictly set to `0.3263`.

## 2. Current Inference Flow
The core inference flow occurs entirely in `src/inference/scorer.py` (`InferenceEngine`):
1. **Request:** `POST /v1/score/merchant` with `merchant_id` and `scoring_timestamp`.
2. **Data Fetch:** Subgraph fetched from `PointInTimeStore`.
3. **Feature Extraction:** `extract_evolution_features(...)` computes temporal, behavioral, and network metrics.
4. **Preprocessing:** Strict `fillna(0)` is applied to the feature dataframe before converting to a NumPy array (`X`).
5. **Prediction:** `probability = float(self.model.predict_proba(X)[0, 1])`.
6. **Threshold Application:** The probability is mapped to `HIGH`, `MEDIUM`, or `LOW` risk bands using `get_risk_band` logic.

## 3. Feature Vector Analysis
* **Extraction Strategy:** Features are extracted strictly up to the `scoring_timestamp` (preventing data leakage).
* **Ordering:** The exact column order is dynamically preserved using `self.feature_cols` from the loaded `model_metadata.json`.
* **Integrity:** The extracted dataframe explicitly drops/ignores sensitive labels like `is_mule` or `merchant_id` before hitting the inference array.

## 4. SHAP Compatibility
* **TreeSHAP Support:** Because the underlying model is an XGBoost Classifier, it is **natively compatible** with `shap.TreeExplainer`. TreeExplainer is extremely fast and exact for tree-based models, avoiding the massive performance overhead of `KernelExplainer`.
* **Observational Guarantee:** SHAP operates strictly on the pre-trained model and the exact feature vector `X` without modifying the model's internal weights or inference path. The prediction score remains byte-for-byte identical.

## 5. Required Dependencies
* **MISSING:** The `shap` library is currently missing from `requirements.txt`.
* **Action Required:** `shap` must be installed (`pip install shap`) before implementation can begin.

## 6. Safe Integration Architecture
To ensure the frozen model remains untouched, the SHAP engine should be wrapped in an independent layer:
* Create a new method `explain_merchant` in `InferenceEngine`.
* This method will call the existing `score_merchant` to get the baseline features, array `X`, and original output.
* It will then instantiate `shap.TreeExplainer(self.model)` (cached for performance) and calculate `shap_values = explainer.shap_values(X)`.
* It will bind the SHAP values back to `self.feature_cols`.

## 7. Proposed API Design
**New Optional Endpoint (Do not mutate existing endpoints):**
`POST /v1/explain/merchant`

**Proposed Response Payload:**
```json
{
  "merchant_id": "M00109",
  "scoring_timestamp": "2026-03-31 00:00:00",
  "risk_score": 87.5,
  "probability": 0.942,
  "risk_band": "HIGH",
  "threshold": 0.3263,
  "base_value": -2.431,
  "explanations": [
    {
      "feature_name": "network_growth_t2_t3",
      "original_value": 0.452,
      "shap_value": 1.25,
      "direction": "INCREASE",
      "rank": 1,
      "category": "NETWORK"
    },
    ...
  ]
}
```

## 8. Proposed Frontend Design
* **Placement:** The "Evidence" tab is the optimal location. 
* **UI Pattern:** Currently, `SmartFeatureRow` displays the raw feature magnitude (e.g., `+45.2% INCREASE`). This should be refactored or augmented to show the **SHAP impact** (e.g., a visual bar indicating how much this specific feature pushed the risk score toward or away from the threshold). 
* **Benefits:** This transforms the raw data points into actionable insights (e.g., "This merchant is flagged *because* their device churn is exceptionally high").

## 9. Performance Considerations
* **Computation Cost:** `TreeExplainer` on a single vector (`N=1`) is highly performant (usually < 10ms).
* **Caching:** The `explainer` object itself should be initialized once during `lifespan` and cached on the `InferenceEngine` to avoid re-parsing the XGBoost trees on every request.
* **Separation:** Keeping `/v1/explain/merchant` separate from `/v1/score/merchant` ensures that bulk timeline operations or network scoring operations do not suffer unnecessary computational overhead.

## 10. Risks & Security
* **Information Disclosure:** Exposing exact SHAP values allows an attacker to probe the API and potentially reverse-engineer the model's feature weights. 
* **Mitigation:** Since this is an *internal risk console* for investigators, this risk is acceptable and necessary for operational transparency. However, this endpoint must NEVER be exposed publicly.

## 11. Files That Must Remain Untouched
* `src/models/mulehunter.py` (No retraining)
* `src/models/model_utils.py` (No threshold or metric changes)
* `data/processed/*` (No dataset changes)

## 12. Files That Would Need Modification
* `requirements.txt` (add `shap`)
* `src/inference/scorer.py` (add `explain_merchant` method and `explainer` cache)
* `src/api/schemas.py` (add `ExplanationResponse` models)
* `src/api/app.py` (expose `/v1/explain/merchant`)
* `dashboard/src/app/merchant/[merchantId]/page.tsx` (update Evidence tab UI)
* `dashboard/src/lib/api.ts` (add `explainMerchant` fetcher)

## 13. Exact Implementation Plan
1. `npm run dev` and `python -m uvicorn ...` must be stopped.
2. Run `pip install shap` and update `requirements.txt`.
3. Implement `explain_merchant` in `scorer.py` using `shap.TreeExplainer`.
4. Define Pydantic schemas in `schemas.py`.
5. Expose the API endpoint in `app.py`.
6. Update the React frontend `api.ts` to call the new endpoint.
7. Modify the `Evidence` tab in `page.tsx` to render the SHAP values as impact bars.

## 14. GO / NO-GO Recommendation
**GO.** 
The architecture is perfectly positioned for a non-destructive SHAP integration. Because the inference logic relies on a strictly ordered array `X`, mapping SHAP values back to the human-readable `self.feature_cols` is trivial and 100% safe. The underlying frozen ML state will remain fully intact.
