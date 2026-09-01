import json
import pickle
from pathlib import Path

def test_model_artifact_exists_and_loads():
    model_path = Path("artifacts/model.pkl")
    assert model_path.exists(), "Model artifact not found"
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    assert hasattr(model, "predict_proba"), "Loaded artifact is not a valid model"

def test_threshold_artifact_exists_and_loads():
    threshold_path = Path("artifacts/threshold.json")
    assert threshold_path.exists(), "Threshold artifact not found"
    
    with open(threshold_path, "r") as f:
        data = json.load(f)
        
    assert "optimal_threshold" in data
    assert isinstance(data["optimal_threshold"], float)

def test_metadata_artifact_exists_and_loads():
    metadata_path = Path("artifacts/model_metadata.json")
    assert metadata_path.exists(), "Metadata artifact not found"
    
    with open(metadata_path, "r") as f:
        data = json.load(f)
        
    required_keys = [
        "model_version",
        "feature_version",
        "training_dataset_version",
        "random_seed",
        "training_split",
        "validation_split",
        "test_split",
        "feature_list",
        "threshold",
        "training_timestamp"
    ]
    
    for key in required_keys:
        assert key in data, f"Metadata missing {key}"
        
    assert len(data["feature_list"]) > 0
