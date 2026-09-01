# Phase 8 Production Audit

## 1. Backend Architecture & Ground Truth Isolation
- **API Contracts:** `app.py` strictly uses Pydantic models (`ScoreResult`, `NetworkScoreResult`, `MerchantMetadataResponse`). 
- **Ground Truth Exposure:** The backend securely isolates ground truth. `PointInTimeStore` loads `merchant_labels.csv` internally for node metadata, but `scorer.py` computes risk probability and only exposes `evidence_features`. The `/v1/merchant/{merchant_id}` metadata endpoint safely queries `merchants.csv` (which lacks labels). **Result:** No labels (`is_mule`, `mule_type`) are leaked to the frontend.

## 2. Model Loading & Production Safety
- **Loading:** `scorer.py` loads `model.pkl` and `model_metadata.json` from disk on initialization (`InferenceEngine.get_instance()`).
- **Retraining Risk:** No training code paths exist in the `src/api/` or `src/inference/` layers. The model is fully frozen.
- **Artifact Constraints:** The threshold is firmly read from `model_metadata.json` and passed verbatim.

## 3. Temporal Leakage Audit
- **Transactions:** `store.py` (`get_merchant_transactions`) filters transactions using `timestamp <= end_ts`.
- **Relationships:** `store.py` (`get_active_relationships`) filters relationships using `start_time <= end_ts`. `evolution_features.py` correctly uses `end_time > window_start` to deduce if a relationship is active in the current window without leaking the exact future termination date. 
- **Risk:** Temporal extraction logic is highly rigid and sound. We will verify this with adversarial temporal tests in Phase 8.

## 4. Frontend Architecture & Dashboard Workflow
- **Hardcoded Elements:** No hardcoded risk scores or fake ML logic exist in the React frontend.
- **Relationships Graph:** The Next.js dashboard uses a star topology around the target merchant because the backend `POST /v1/score/network` explicitly returns scored neighbor objects but omits specific infrastructure edge data (IPs/Devices). This correctly avoids hallucinating edges.

## 5. Performance Bottlenecks
- **Backend Latency:** `store.py:get_network_subgraph()` performs sequential Pandas DataFrame filtering (3 passes). This results in ~2s latency for 90-day subgraphs. 
- **Frontend Load:** The `MerchantInvestigationPage` makes up to 5 concurrent API calls (Metadata, Current Score, Timeline, Network, Model Metadata). While parallelized (`Promise.all`), the total time is bound by the slowest `NetworkScore` or `Timeline` call (~2.5-3.5s total).

## 6. Audit Conclusion & Next Steps
The codebase fundamentally adheres to the required Phase 7 constraints. Phase 8 will focus on:
1. Adding temporal safety adversarial tests.
2. Grouping risk evidence neatly on the frontend (already largely addressed in Phase 7).
3. Adding the `demo_health_check.py` script.
4. Completing full validation reporting.
