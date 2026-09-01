# Frontend Integration Audit

## Available Endpoints & Schemas

### 1. `GET /health`
- **Request:** None
- **Response:** `{"status": "ok"}`
- **Usage:** Dashboard system status indicator.

### 2. `GET /model/metadata`
- **Request:** None
- **Response:** `ModelMetadataResponse` (`version`, `threshold`, `feature_list`, `training_timestamp`)
- **Usage:** Displaying frozen model threshold and version.

### 3. `GET /v1/merchant/{merchant_id}`
- **Request:** Path parameter `merchant_id`
- **Response:** `MerchantMetadataResponse` (`merchant_id`, `merchant_name`, `category`, `onboarding_date`, `kyc_status`)
- **Security:** Sanitized. No `is_mule`, `network_id`, or ground-truth labels exposed.
- **Usage:** Merchant investigation header.

### 4. `POST /v1/score/merchant`
- **Request:** `ScoreRequest` (`merchant_id`, `scoring_timestamp`)
- **Response:** `ScoreResult` (`merchant_id`, `scoring_timestamp`, `risk_score`, `probability`, `risk_band`, `behavioral_risk`, `network_risk`, `evidence_features`)
- **Usage:** Fetching point-in-time risk score and evidence features.

### 5. `POST /v1/score/network`
- **Request:** `ScoreRequest` (`merchant_id`, `scoring_timestamp`)
- **Response:** `NetworkScoreResult` (`merchant_id`, `results: List[ScoreResult]`)
- **Usage:** Fetching scored 1-hop neighboring merchants.

### 6. `POST /v1/score/merchant/timeline`
- **Request:** `TimelineScoreRequest` (`merchant_id`, `scoring_timestamps: List[str]`)
- **Response:** `List[ScoreResult]`
- **Usage:** Recharts timeline visualization.

## Missing Dependencies & Limitations
- **Network Relationship Edges:** The backend does **not** expose a `/v1/network/{merchant_id}/relationships` endpoint. `POST /v1/score/network` returns neighbor nodes but omits the explicit shared entities connecting them (e.g., shared IPs, devices). 
- **Frontend Mitigation:** Following instructions, the React Flow visualization will render a simplified star-topology graph (Central Merchant connected directly to Neighboring Merchants via generic 'Shared Entity' edges), rather than fabricating explicit IP/Device relationship data.
- **Recent Investigations:** There is no persistent database of recent searches. The frontend will prompt the user to "Search a merchant to begin investigation."
