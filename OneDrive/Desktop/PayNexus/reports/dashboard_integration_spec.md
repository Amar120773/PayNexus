# Dashboard Integration Specification

## 1. Current Backend Architecture
The backend is a FastAPI microservice that provides point-in-time inference capabilities over a synthetic transaction network. Data access is abstracted via `PointInTimeStore`, which simulates a graph database queries with strict temporal bounds.

## 2. Existing Endpoints
- `GET /health`: Returns service health status.
- `GET /model/metadata`: Returns model version, frozen threshold (0.3263), feature list, and training timestamp.
- `POST /v1/score/merchant`: Evaluates a single merchant at a specific point in time. 
- `POST /v1/score/network`: Evaluates a merchant and its 1-hop point-in-time neighborhood.
- `GET /v1/monitoring/blind-spots`: Returns the latest pre-computed blind-spot analysis report.

## 3. Existing Schemas
- `ScoreRequest`: `merchant_id`, `scoring_timestamp`
- `ScoreResult`: `merchant_id`, `scoring_timestamp`, `risk_score`, `probability`, `risk_band`, `behavioral_risk`, `network_risk`, `evidence_features`
- `NetworkScoreResult`: `merchant_id`, list of `ScoreResult`
- `ModelMetadataResponse`, `BlindSpotResponse`

## 4. Point-in-Time Guarantees
All existing POST scoring endpoints query the `PointInTimeStore.get_network_subgraph()`, which enforces strict lookback windows (e.g., 90 days for transactions, 30 days for active relationships). Information strictly after the `scoring_timestamp` is entirely excluded before reaching the `InferenceEngine`.

## 5. Model Artifact Loading
The `InferenceEngine` loads frozen artifacts (`artifacts/model.pkl` and `artifacts/model_metadata.json`) dynamically via an `asynccontextmanager` on FastAPI startup. The threshold is strictly fixed at `0.3263`.

## 6. Dashboard Limitations and Missing Features
- **Historical Timeline:** Currently, fetching historical scores requires multiple sequential HTTP requests from the client.
- **Sanitized Metadata:** The client has no endpoint to fetch basic merchant profile details (e.g., onboard date) safely. 

## 7. Files Required for Modification
- `src/api/schemas.py`: Define `TimelineScoreRequest` and `MerchantMetadataResponse`.
- `src/api/app.py`: Implement `POST /v1/score/merchant/timeline` and `GET /v1/merchant/{merchant_id}` routes.

## 8. Files That MUST NOT Be Modified
- `src/models/*`
- `src/features_v2/*`
- `src/inference/scorer.py`
- `src/inference/store.py`
- `artifacts/model.pkl`, `artifacts/model_metadata.json`
- `data/*`
