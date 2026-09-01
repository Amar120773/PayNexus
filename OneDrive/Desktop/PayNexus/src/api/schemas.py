from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class ScoreRequest(BaseModel):
    merchant_id: str = Field(..., description="The ID of the merchant to score")
    scoring_timestamp: str = Field(..., description="The strict point-in-time timestamp (YYYY-MM-DD HH:MM:SS) for evaluation")

class ScoreResult(BaseModel):
    merchant_id: str
    scoring_timestamp: str
    risk_score: float
    probability: float
    risk_band: str
    behavioral_risk: Optional[float] = None
    network_risk: Optional[float] = None
    evidence_features: Dict[str, float]

class NetworkScoreResult(BaseModel):
    merchant_id: str
    results: List[ScoreResult]

class ModelMetadataResponse(BaseModel):
    version: str
    threshold: float
    feature_list: List[str]
    training_timestamp: str

class BlindSpotResponse(BaseModel):
    scoring_timestamp: str
    global_metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    recall_degradation: Dict[str, Any]
    segment_metrics: List[Dict[str, Any]]
    fn_concentration: List[Dict[str, Any]]
    feature_drift: List[Dict[str, Any]]
    blind_spots: List[Dict[str, Any]]

class TimelineScoreRequest(BaseModel):
    merchant_id: str = Field(..., description="The ID of the merchant to score")
    scoring_timestamps: List[str] = Field(..., description="A list of strict point-in-time timestamps for evaluation")

class MerchantMetadataResponse(BaseModel):
    merchant_id: str
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    onboarding_date: Optional[str] = None
    kyc_status: Optional[str] = None

class ExplanationFeature(BaseModel):
    feature_name: str
    original_value: float
    shap_value: float
    direction: str
    rank: int
    category: Optional[str] = None

class ExplanationResponse(BaseModel):
    merchant_id: str
    scoring_timestamp: str
    risk_score: float
    probability: float
    risk_band: str
    threshold: float
    base_value: float
    explanations: List[ExplanationFeature]
