"""Point-in-time inference scorer for MuleHunter V2."""

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import networkx as nx

from src.features_v2.evolution_features import extract_evolution_features
from src.models.model_utils import compute_risk_score
from src.explainability.shap_explainer import ShapExplainer

class InferenceEngine:
    _instance = None

    def __init__(self, artifacts_dir: Path | str = "artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.model = None
        self.metadata = None
        self.threshold = None
        self.feature_cols = None
        self.explainer = None
        self._load_artifacts()

    @classmethod
    def get_instance(cls, artifacts_dir: Path | str = "artifacts") -> "InferenceEngine":
        if cls._instance is None:
            cls._instance = cls(artifacts_dir)
        return cls._instance

    def _load_artifacts(self) -> None:
        model_path = self.artifacts_dir / "model.pkl"
        metadata_path = self.artifacts_dir / "model_metadata.json"
        
        if not model_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"Model artifacts not found in {self.artifacts_dir}")
            
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
            
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)
            
            
        self.threshold = self.metadata["threshold"]
        self.feature_cols = self.metadata["feature_list"]
        self.explainer = ShapExplainer.get_instance(self.model, self.feature_cols)

    def get_risk_band(self, probability: float) -> str:
        """Assign risk band based on frozen threshold."""
        if probability >= self.threshold:
            if probability >= min(self.threshold * 1.5, 0.9):
                return "HIGH"
            return "MEDIUM"
        return "LOW"

    def score_merchant(
        self,
        merchant_id: str,
        scoring_timestamp: str,
        merchants: pd.DataFrame,
        transactions: pd.DataFrame,
        relationships: pd.DataFrame
    ) -> dict[str, Any]:
        """Score a single merchant safely at a specific point in time."""
        
        # Guard against label leakage (is_mule, network_id, mule_type must NOT be passed in feature computation)
        # The extract_evolution_features doesn't use them, but we ensure they aren't somehow sneaked into model
        
        features_df = extract_evolution_features(
            merchants=merchants,
            transactions=transactions,
            relationships=relationships,
            scoring_timestamp_str=scoring_timestamp,
            valid_merchants=[merchant_id]
        )
        
        if len(features_df) == 0:
            raise ValueError(f"Merchant {merchant_id} not found or has no data.")
            
        row = features_df.iloc[0]
        
        # Prepare feature vector
        X = features_df[self.feature_cols].fillna(0).to_numpy()
        
        probability = float(self.model.predict_proba(X)[0, 1])
        risk_score = compute_risk_score(np.array([probability]))[0]
        risk_band = self.get_risk_band(probability)
        
        # For simplicity in V2 MVP, behavior vs network vs evolution is inferred from specific features
        behavioral_risk = float(row.get("volume_delta_t2_t3", 0.0))
        network_risk = float(row.get("network_growth_t2_t3", 0.0))
        
        evidence_features = {col: float(row[col]) for col in self.feature_cols}
        
        return {
            "merchant_id": merchant_id,
            "scoring_timestamp": scoring_timestamp,
            "risk_score": float(risk_score),
            "probability": probability,
            "risk_band": risk_band,
            "behavioral_risk": behavioral_risk,
            "network_risk": network_risk,
            "evidence_features": evidence_features
        }

    def explain_merchant(
        self,
        merchant_id: str,
        scoring_timestamp: str,
        merchants: pd.DataFrame,
        transactions: pd.DataFrame,
        relationships: pd.DataFrame
    ) -> dict[str, Any]:
        """Generate SHAP explanation while reusing the existing prediction logic."""
        
        # 1. First run the normal scoring to get the verified output and the exact feature vector
        features_df = extract_evolution_features(
            merchants=merchants,
            transactions=transactions,
            relationships=relationships,
            scoring_timestamp_str=scoring_timestamp,
            valid_merchants=[merchant_id]
        )
        
        if len(features_df) == 0:
            raise ValueError(f"Merchant {merchant_id} not found or has no data.")
            
        row = features_df.iloc[0]
        
        # Exact vector X
        X = features_df[self.feature_cols].fillna(0).to_numpy()
        
        # Original probability / band logic
        probability = float(self.model.predict_proba(X)[0, 1])
        risk_score = compute_risk_score(np.array([probability]))[0]
        risk_band = self.get_risk_band(probability)
        
        original_features = {col: float(row[col]) for col in self.feature_cols}
        
        # 2. Run SHAP on the exact same X
        explanation_data = self.explainer.explain(X, original_features)
        
        return {
            "merchant_id": merchant_id,
            "scoring_timestamp": scoring_timestamp,
            "risk_score": float(risk_score),
            "probability": probability,
            "risk_band": risk_band,
            "threshold": self.threshold,
            "base_value": explanation_data["base_value"],
            "explanations": explanation_data["explanations"]
        }

    def score_network(
        self,
        merchant_id: str,
        scoring_timestamp: str,
        merchants: pd.DataFrame,
        transactions: pd.DataFrame,
        relationships: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """Score a merchant and its 1-hop point-in-time neighborhood."""
        scoring_ts = pd.Timestamp(scoring_timestamp)
        
        # Extract active graph at T
        # Only relationships up to scoring_timestamp and active within the last 30 days of scoring_timestamp
        rels = relationships[relationships["start_time"] <= scoring_ts].copy()
        
        # Strict window start
        window_start = scoring_ts - pd.Timedelta(days=30)
        active_rels = rels[(rels["start_time"] < scoring_ts) & (rels["end_time"] > window_start)]
        
        # Bipartite projection to find 1-hop neighbors
        G = nx.Graph()
        G.add_nodes_from(active_rels["merchant_id"].unique(), bipartite=0)
        
        edges = []
        for _, row in active_rels.iterrows():
            edges.append((row["merchant_id"], row["entity_id"]))
            
        G.add_edges_from(edges)
        
        if merchant_id not in G:
            # Isolated merchant or no active relationships
            network_merchants = [merchant_id]
        else:
            network_merchants = set([merchant_id])
            for entity in G.neighbors(merchant_id):
                for neighbor_m in G.neighbors(entity):
                    network_merchants.add(neighbor_m)
            network_merchants = list(network_merchants)
            
        features_df = extract_evolution_features(
            merchants=merchants,
            transactions=transactions,
            relationships=relationships,
            scoring_timestamp_str=scoring_timestamp,
            valid_merchants=network_merchants
        )
        
        X = features_df[self.feature_cols].fillna(0).to_numpy()
        probs = self.model.predict_proba(X)[:, 1]
        scores = compute_risk_score(probs)
        
        results = []
        for i, m_id in enumerate(features_df["merchant_id"]):
            results.append({
                "merchant_id": m_id,
                "scoring_timestamp": scoring_timestamp,
                "risk_score": float(scores[i]),
                "probability": float(probs[i]),
                "risk_band": self.get_risk_band(probs[i]),
                "evidence_features": {col: float(features_df.iloc[i][col]) for col in self.feature_cols}
            })
            
        return results

    def find_first_detection(
        self,
        merchant_id: str,
        merchants: pd.DataFrame,
        transactions: pd.DataFrame,
        relationships: pd.DataFrame,
        candidate_timestamps: list[str]
    ) -> str | None:
        """Find the earliest timestamp where the merchant crossed the threshold."""
        for ts in sorted(candidate_timestamps):
            try:
                res = self.score_merchant(merchant_id, ts, merchants, transactions, relationships)
                if res["probability"] >= self.threshold:
                    return ts
            except ValueError:
                continue
        return None

def score_merchant(merchant_id, scoring_timestamp, merchants, transactions, relationships):
    engine = InferenceEngine.get_instance()
    return engine.score_merchant(merchant_id, scoring_timestamp, merchants, transactions, relationships)

def explain_merchant(merchant_id, scoring_timestamp, merchants, transactions, relationships):
    engine = InferenceEngine.get_instance()
    return engine.explain_merchant(merchant_id, scoring_timestamp, merchants, transactions, relationships)

def score_network(merchant_id, scoring_timestamp, merchants, transactions, relationships):
    engine = InferenceEngine.get_instance()
    return engine.score_network(merchant_id, scoring_timestamp, merchants, transactions, relationships)
