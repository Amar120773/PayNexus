from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from pathlib import Path
import os

from src.api.schemas import ScoreRequest, ScoreResult, NetworkScoreResult, ModelMetadataResponse, BlindSpotResponse, TimelineScoreRequest, MerchantMetadataResponse, ExplanationResponse
from src.inference.scorer import InferenceEngine
from src.inference.store import PointInTimeStore
from src.monitoring.blind_spot import BlindSpotReport
import pandas as pd
from functools import lru_cache

# Global instances
engine: InferenceEngine = None
store: PointInTimeStore = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, store
    # Load ML models and metadata
    engine = InferenceEngine.get_instance()
    # Load data store
    store = PointInTimeStore.get_instance()
    
    yield
    # Cleanup if necessary

app = FastAPI(
    title="PayNexus API",
    version="2.0.0",
    description="Point-in-time fraud inference service.",
    lifespan=lifespan
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check() -> Dict[str, str]:
    if engine is None or store is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    return {"status": "ok"}

@lru_cache(maxsize=128)
def _cached_network_subgraph(merchant_id: str, scoring_timestamp: str):
    """Internal cache to prevent redundant Neo4j Cypher queries for the same point-in-time."""
    return store.get_network_subgraph(merchant_id, scoring_timestamp)

def get_defensive_subgraph(merchant_id: str, scoring_timestamp: str):
    """Returns defensive copies of cached DataFrames to prevent inplace mutation leakage."""
    m_df, tx_df, rels_df = _cached_network_subgraph(merchant_id, scoring_timestamp)
    return m_df.copy(), tx_df.copy(), rels_df.copy()

@app.get("/model/metadata", response_model=ModelMetadataResponse)
def get_model_metadata():
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not loaded")
    return ModelMetadataResponse(
        version="v2",
        threshold=engine.threshold,
        feature_list=engine.feature_cols,
        training_timestamp="Frozen Phase 4B"
    )

@app.post("/v1/score/merchant", response_model=ScoreResult)
def score_merchant_endpoint(req: ScoreRequest):
    """
    Score a single merchant safely at a specific point in time.
    """
    try:
        # 1. Fetch exact temporal subgraph for this merchant
        m_df, tx_df, rels_df = get_defensive_subgraph(req.merchant_id, req.scoring_timestamp)
        
        # 2. Check existence
        if m_df.empty:
            raise HTTPException(status_code=404, detail=f"Merchant {req.merchant_id} not found in store.")
            
        # 3. Pass to the existing scorer without modifying scorer signature
        res = engine.score_merchant(
            merchant_id=req.merchant_id,
            scoring_timestamp=req.scoring_timestamp,
            merchants=m_df,
            transactions=tx_df,
            relationships=rels_df
        )
        return ScoreResult(**res)
    except HTTPException:
        raise
    except ValueError as e:
        if "not found or has no data" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Inference Error")

@app.post("/v1/explain/merchant", response_model=ExplanationResponse)
def explain_merchant_endpoint(req: ScoreRequest):
    """
    Generate SHAP explanation for a merchant safely at a specific point in time.
    """
    try:
        # 1. Fetch exact temporal subgraph for this merchant
        m_df, tx_df, rels_df = get_defensive_subgraph(req.merchant_id, req.scoring_timestamp)
        
        # 2. Check existence
        if m_df.empty:
            raise HTTPException(status_code=404, detail=f"Merchant {req.merchant_id} not found in store.")
            
        # 3. Pass to the existing explain method without modifying scorer signature
        res = engine.explain_merchant(
            merchant_id=req.merchant_id,
            scoring_timestamp=req.scoring_timestamp,
            merchants=m_df,
            transactions=tx_df,
            relationships=rels_df
        )
        return ExplanationResponse(**res)
    except HTTPException:
        raise
    except ValueError as e:
        if "not found or has no data" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Explain Error: {str(e)}")

@app.post("/v1/score/network", response_model=NetworkScoreResult)
def score_network_endpoint(req: ScoreRequest):
    """
    Score a merchant and its 1-hop point-in-time neighborhood.
    """
    try:
        # 1. Fetch exact temporal subgraph for this merchant's network
        m_df, tx_df, rels_df = get_defensive_subgraph(req.merchant_id, req.scoring_timestamp)
        
        # 2. Check existence
        if m_df.empty:
            raise HTTPException(status_code=404, detail=f"Merchant {req.merchant_id} not found in store.")
            
        # 3. Pass to existing scorer
        results = engine.score_network(
            merchant_id=req.merchant_id,
            scoring_timestamp=req.scoring_timestamp,
            merchants=m_df,
            transactions=tx_df,
            relationships=rels_df
        )
        return NetworkScoreResult(merchant_id=req.merchant_id, results=results)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Inference Error")

BLIND_SPOT_REPORT_PATH = Path("artifacts/blind_spot_report.json")

@app.get("/v1/monitoring/blind-spots", response_model=BlindSpotResponse)
def get_blind_spot_report():
    """Return the latest pre-computed blind-spot analysis report."""
    if not BLIND_SPOT_REPORT_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No blind-spot report available. Run the monitoring analysis first."
        )
    try:
        report = BlindSpotReport.load(BLIND_SPOT_REPORT_PATH)
        return BlindSpotResponse(**report.to_dict())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load blind-spot report.")

@app.post("/v1/score/merchant/timeline", response_model=list[ScoreResult])
def score_merchant_timeline(req: TimelineScoreRequest):
    """
    Score a single merchant sequentially over a list of point-in-time timestamps.
    """
    # 1. Ensure merchant exists in the database
    if store.get_merchant(req.merchant_id).empty:
        raise HTTPException(status_code=404, detail=f"Merchant {req.merchant_id} not found in store.")
        
    sorted_timestamps = sorted(req.scoring_timestamps)
    results = []
    
    for ts in sorted_timestamps:
        try:
            m_df, tx_df, rels_df = get_defensive_subgraph(req.merchant_id, ts)
            
            res = engine.score_merchant(
                merchant_id=req.merchant_id,
                scoring_timestamp=ts,
                merchants=m_df,
                transactions=tx_df,
                relationships=rels_df
            )
            results.append(ScoreResult(**res))
        except ValueError as e:
            if "not found or has no data" in str(e).lower():
                continue # Skip timestamps before merchant had activity
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal Inference Error")
            
    return results

@app.get("/v1/merchant/{merchant_id}", response_model=MerchantMetadataResponse)
def get_merchant_metadata(merchant_id: str):
    """
    Return sanitized metadata for a merchant directly from Neo4j.
    """
    m_info = store.get_merchant(merchant_id)
    if m_info.empty:
        raise HTTPException(status_code=404, detail="Merchant not found")
        
    row = m_info.iloc[0]
    
    return MerchantMetadataResponse(
        merchant_id=str(row["merchant_id"]),
        merchant_name=str(row.get("merchant_name", "")),
        category=str(row.get("category", "")),
        onboarding_date=str(row.get("onboarding_date", "")),
        kyc_status=str(row.get("kyc_status", ""))
    )
