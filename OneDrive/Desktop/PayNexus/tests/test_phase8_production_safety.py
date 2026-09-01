import pytest
from src.inference.scorer import InferenceEngine
from src.api.schemas import ScoreResult, NetworkScoreResult

def test_frozen_model_loads_without_training():
    """Verify the inference engine loads the pre-trained artifact safely without retraining."""
    engine = InferenceEngine.get_instance()
    
    assert engine.model is not None, "Model failed to load."
    assert engine.threshold is not None, "Threshold failed to load."
    assert isinstance(engine.threshold, float), "Threshold must be a float."
    assert engine.threshold == pytest.approx(0.3263, abs=1e-3), "FROZEN THRESHOLD WAS MODIFIED! This violates Phase 8 rules."
    
def test_ground_truth_isolation():
    """Verify that ScoreResult API schema NEVER exposes ground-truth labels."""
    schema_fields = ScoreResult.model_fields.keys()
    
    assert "is_mule" not in schema_fields, "CRITICAL LEAK: is_mule exposed in API response!"
    assert "mule_type" not in schema_fields, "CRITICAL LEAK: mule_type exposed in API response!"
    assert "network_id" not in schema_fields, "CRITICAL LEAK: network_id exposed in API response!"

def test_frontend_independence():
    """Verify that the frontend cannot mathematically recalculate risk by ensuring raw features aren't passed."""
    # The frontend is given 'evidence_features', which is aggregated static numbers.
    # It is NOT given raw transaction arrays or raw node embeddings.
    schema_fields = ScoreResult.model_fields.keys()
    
    assert "transactions" not in schema_fields, "Raw transactions exposed!"
    assert "relationships" not in schema_fields, "Raw relationships exposed!"
    # Ensures risk calculation happens ONLY on backend.
