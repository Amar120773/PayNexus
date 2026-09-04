"""SHAP Explainer for MuleHunter V2."""

import logging
from typing import Any
import numpy as np
import builtins

try:
    import shap
except ImportError:
    shap = None

logger = logging.getLogger(__name__)

class ShapExplainer:
    """Safe, read-only SHAP explainer for the frozen MuleHunter V2 model."""

    _instance = None

    def __init__(self, model: Any, feature_cols: list[str]):
        if shap is None:
            raise ImportError("SHAP library is not installed.")
        
        self.model = model
        self.feature_cols = feature_cols
        
        # Initialize TreeExplainer once
        # Using feature_perturbation="tree_path_dependent" by default for XGBoost, which doesn't require a background dataset
        
        # Workaround for XGBoost > 2.0 and SHAP base_score parsing bug
        original_float = builtins.float
        class patched_float(float):
            def __new__(cls, x=0):
                if isinstance(x, str) and x.startswith('[') and x.endswith(']'):
                    x = x[1:-1]
                return original_float(x)
        
        try:
            builtins.float = patched_float
            self.explainer = shap.TreeExplainer(self.model)
        finally:
            builtins.float = original_float
        
        # The expected value (base value) in margin space
        # TreeExplainer expected_value can be an array if multi-class, or single float if binary/margin
        if isinstance(self.explainer.expected_value, (np.ndarray, list)):
            self.base_value = float(self.explainer.expected_value[0])
        else:
            self.base_value = float(self.explainer.expected_value)

    @classmethod
    def get_instance(cls, model: Any, feature_cols: list[str]) -> "ShapExplainer":
        if cls._instance is None:
            cls._instance = cls(model, feature_cols)
        return cls._instance

    def explain(self, X: np.ndarray, original_features: dict[str, float]) -> dict[str, Any]:
        """
        Explain the exact feature vector X used by inference.
        Returns base_value and a list of structured explanations.
        """
        # SHAP outputs values in the raw margin space (log-odds) for XGBoost
        shap_values = self.explainer.shap_values(X)
        
        # For a single prediction, shap_values is typically 1D or 2D (1, num_features)
        if len(shap_values.shape) > 1:
            contributions = shap_values[0]
        else:
            contributions = shap_values
            
        explanations = []
        for i, col in enumerate(self.feature_cols):
            val = float(contributions[i])
            direction = "INCREASE" if val > 0 else ("DECREASE" if val < 0 else "NEUTRAL")
            
            explanations.append({
                "feature_name": col,
                "original_value": original_features.get(col, 0.0),
                "shap_value": val,
                "direction": direction,
                "abs_magnitude": abs(val)
            })
            
        # Rank by absolute magnitude descending
        explanations.sort(key=lambda x: x["abs_magnitude"], reverse=True)
        
        # Assign rank and remove the temporary abs_magnitude
        for idx, exp in enumerate(explanations):
            exp["rank"] = idx + 1
            del exp["abs_magnitude"]
            
        return {
            "base_value": self.base_value,
            "explanations": explanations
        }
