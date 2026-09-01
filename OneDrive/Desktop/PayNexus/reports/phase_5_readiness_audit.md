# Phase 4B → Phase 5 Readiness Audit

## Overview
Phase 4B successfully migrated the V2 research pipeline into a strictly point-in-time, serialized inference engine. We now have guaranteed zero-leakage offline evaluation. However, the current architecture is designed for batch/offline usage and must be adapted for a live, production-like microservice in Phase 5.

## 1. Data Access Bottleneck (Critical Gap)
**Current State:** 
The `InferenceEngine` methods (`score_merchant`, `score_network`) require full, in-memory Pandas DataFrames (`merchants`, `transactions`, `relationships`) to be passed as arguments.
**Production Requirement:**
A live service cannot load or accept multi-gigabyte dataframes per request. We need a Data Access Layer (DAL) or a simulated point-in-time database connector.
**Recommendation:**
Introduce a `PointInTimeStore` interface (e.g., `src/inference/store.py`) that abstracts data fetching. The service will query this store to return only the subset of transactions and relationships relevant to the requested `merchant_id` and `scoring_timestamp`.

## 2. Graph Construction Inefficiency
**Current State:**
In `score_network` and `extract_evolution_features`, the code filters the entire `relationships` dataframe to build `G(T)`. 
**Production Requirement:**
For a single merchant request, constructing a global graph from all active edges across the entire network is computationally prohibitive.
**Recommendation:**
The DAL should support localized queries (e.g., "Get all relationships for Merchant M and its shared entities within the last 30 days"). The graph should be built as a local ego-graph centered around the target merchant(s).

## 3. Missing Service API Layer
**Current State:**
The inference engine is invoked directly via Python function calls.
**Production Requirement:**
The engine must be wrapped in a production-ready web framework to serve incoming requests over HTTP.
**Recommendation:**
Implement a REST API using FastAPI (`src/api/app.py`). It should expose endpoints like:
- `POST /v1/score/merchant`
- `POST /v1/score/network`
The FastAPI application will load the `InferenceEngine` singleton on startup.

## 4. Configuration and Environment Management
**Current State:**
Paths to artifacts are hardcoded to `artifacts/` or passed directly.
**Production Requirement:**
The service should be configurable via environment variables or a configuration file.
**Recommendation:**
Add a `config.py` in the API layer utilizing `pydantic` BaseSettings to manage the artifact directory paths, port numbers, and datastore paths.

## Summary of Readiness
The mathematical and logical foundation (anti-leakage) is **ready** and proven by the test suite. The architectural foundation is **not ready** for real-time serving due to its reliance on in-memory batch processing and lack of an API transport layer. Phase 5 will address these infrastructure gaps.
