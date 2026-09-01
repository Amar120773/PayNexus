# MuleHunter Final System Architecture

This document describes the architectural layout of the MuleHunter / PayNexus system, intentionally partitioned between the frozen research pipeline and the live production/demo systems.

## 1. Research System (Frozen)
The ML pipeline is completely detached from the live API. It consists of:
- **Data Generation:** `synthetic_v2` dataset containing relationships, transactions, and ground truth (`merchant_labels.csv`).
- **Graph Construction:** Bipartite projections connecting merchants via shared infrastructure.
- **Model Training:** LightGBM classifier frozen during Phase 4 (`artifacts/model.pkl`).
- **Research Evaluation:** Static threshold derivation (`0.3263`), blind spot analysis (identifying Type-D evasion patterns), and performance bounding.

## 2. Demo/Inference System (Active)
The production API and Dashboard operate purely as consumers of the frozen artifacts.

### Data Layer (`src/inference/store.py`)
- **Point-In-Time Store:** Simulates a production data warehouse. 
- **Temporal Enforcement:** Guarantees that any query at `scoring_timestamp = T` mathematically excludes transactions with `timestamp > T` and relationships with `start_time > T`.

### Feature Extraction (`src/features_v2/evolution_features.py`)
- Executes the identical feature calculation logic used in research, but enforces the 30-day bounded temporal windows (`T1`, `T2`, `T3`) relative to the dynamic user-requested `scoring_timestamp`. 

### Risk Scoring (`src/inference/scorer.py`)
- **Inference Engine:** A singleton that loads the frozen `model.pkl` and `model_metadata.json` upon API startup.
- **Ground Truth Isolation:** Automatically strips ground truth labels (`is_mule`) so they cannot accidentally bleed into the inference output.

### FastAPI Service (`src/api/app.py`)
- Handles endpoint routing for `/score/merchant`, `/score/network`, and `/score/merchant/timeline`.
- Utilizes strict Pydantic schemas (`ScoreResult`, `NetworkScoreResult`) to ensure the response payload only includes necessary visualizer evidence, not raw calculation parameters.

### Next.js Dashboard (`dashboard/`)
- **Investigator Workflow:** Search -> Overview -> Case Summary -> Temporal Timeline -> Network Graph.
- **Stateless UI:** The frontend holds no ML logic. Risk bands, scores, probabilities, and temporal evidence metrics are completely calculated by FastAPI and purely displayed by React Flow and Recharts.

## 3. Known Limitations
- **Type-D Evasion:** The feature extraction relies on 30-day temporal windows. Slow-burn illicit actors (Type-D) can wait out the window reset to drop their risk score below the threshold. The dashboard mitigates this by providing a continuous historical timeline and visual network graph.
- **Performance:** Subgraph extraction over the synthetic transaction graph takes ~2s. This is sufficient for single-investigator demos but would require aggressive materialized views for a large-scale live system.
