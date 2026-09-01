# MuleHunter: Architecture Diagram Specification

This document specifies the architecture diagrams needed for the Razorpay Buildathon presentation.

---

## Diagram 1: End-to-End Inference Pipeline

This is the primary diagram. It shows the flow from raw data to investigator action.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                    │
│                                                                      │
│  Merchants          Transactions          Relationships              │
│  (5,000)            (150,000)             (Device, IP Edges)         │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  POINT-IN-TIME STORE                                 │
│                  src/inference/store.py                               │
│                                                                      │
│  Input: merchant_id + scoring_timestamp                              │
│  Output: Temporally filtered subgraph (merchants, tx, rels)          │
│  Guarantee: timestamp > scoring_timestamp is EXCLUDED                │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│              TEMPORAL GRAPH CONSTRUCTION                              │
│              src/features_v2/evolution_features.py                    │
│                                                                      │
│  T1 (Days 1–30)    T2 (Days 31–60)    T3 (Days 61–90)              │
│       │                  │                  │                        │
│       └───── Δ₁ ────────┘                  │                        │
│                          └───── Δ₂ ────────┘                        │
│                                                                      │
│  ┌──────────────────┬──────────────────┬──────────────────┐         │
│  │ BEHAVIORAL       │ NETWORK          │ TEMPORAL         │         │
│  │ volume_delta     │ network_growth   │ device_churn     │         │
│  │ refund_delta     │                  │ ip_churn         │         │
│  └──────────────────┴──────────────────┴──────────────────┘         │
│                                                                      │
│  Output: 10-dimensional feature vector per merchant                  │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                FROZEN MULEHUNTER MODEL                                │
│                artifacts/model.pkl                                    │
│                                                                      │
│  Type: LightGBM Classifier                                          │
│  Threshold: 0.3263 (frozen)                                          │
│  Output: probability → risk_score → risk_band                        │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVICE                                    │
│                    src/api/app.py                                     │
│                                                                      │
│  POST /v1/score/merchant      → ScoreResult                         │
│  POST /v1/score/network       → NetworkScoreResult                   │
│  POST /v1/score/merchant/timeline → [ScoreResult]                    │
│  GET  /v1/merchant/{id}       → MerchantMetadata                     │
│  GET  /model/metadata         → ModelMetadata                        │
│  GET  /health                 → HealthCheck                          │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│              INVESTIGATOR DASHBOARD                                   │
│              Next.js + React Flow + Recharts                         │
│                                                                      │
│  ┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │Dashboard│→ │Merchant     │→ │Risk      │→ │Network           │  │
│  │Overview │  │Investigation│  │Timeline  │  │Intelligence      │  │
│  └─────────┘  └─────────────┘  └──────────┘  └──────────────────┘  │
│                                                                      │
│  NO ML LOGIC IN FRONTEND — displays backend-produced values only     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Diagram 2: Research vs. Inference Pipeline Separation

This diagram clarifies the boundary between the frozen research system and the live inference system.

```
┌─────────────────────────────────────────────┐
│           RESEARCH PIPELINE (FROZEN)         │
│                                              │
│  Dataset Generation                          │
│       ↓                                      │
│  Synthetic V2 Data (5,000 merchants)         │
│       ↓                                      │
│  Feature Engineering Experiments             │
│  (5-way ablation, leakage remediation)       │
│       ↓                                      │
│  Model Training (XGBoost / LightGBM)         │
│       ↓                                      │
│  Evaluation (network-isolated held-out)      │
│       ↓                                      │
│  Blind-Spot Analysis (Type A–D)              │
│       ↓                                      │
│  ┌─────────────────────────────────────┐     │
│  │       FROZEN ARTIFACTS              │     │
│  │  model.pkl                          │     │
│  │  model_metadata.json (threshold)    │     │
│  │  threshold.json                     │     │
│  └──────────────┬──────────────────────┘     │
│                 │                             │
└─────────────────┼─────────────────────────────┘
                  │ serialized artifacts
                  │ (one-way, read-only)
                  ▼
┌─────────────────────────────────────────────┐
│         INFERENCE PIPELINE (ACTIVE)          │
│                                              │
│  PointInTimeStore (temporal data access)     │
│       ↓                                      │
│  InferenceEngine (loads frozen model)        │
│       ↓                                      │
│  FastAPI Service (REST endpoints)            │
│       ↓                                      │
│  Next.js Dashboard (stateless UI)            │
│                                              │
│  GUARANTEES:                                 │
│  • No retraining paths                       │
│  • No ground-truth exposure                  │
│  • No future data leakage                    │
│  • Frontend cannot recalculate risk          │
└─────────────────────────────────────────────┘
```

---

## Key Design Principles

1. **One-way artifact flow**: The research pipeline produces serialized artifacts. The inference pipeline consumes them read-only. There is no feedback loop.
2. **Temporal guarantees**: Every query specifies a scoring timestamp. The PointInTimeStore enforces that no data after that timestamp enters the feature computation.
3. **Ground-truth isolation**: Research labels (`is_mule`, `mule_type`, `network_id`) exist only in the research pipeline. The inference pipeline and dashboard never expose them.
4. **Stateless frontend**: The dashboard holds zero ML logic. Risk scores, risk bands, evidence features, and temporal trajectories are all computed server-side by the FastAPI endpoints and displayed as-received.
