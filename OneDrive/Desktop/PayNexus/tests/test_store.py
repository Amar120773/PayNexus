import pytest
import os
from unittest.mock import patch
from src.inference.store import PointInTimeStore

@pytest.fixture(autouse=True)
def reset_store():
    # Reset singleton before and after each test
    PointInTimeStore._instance = None
    yield
    PointInTimeStore._instance = None

def test_store_fails_closed_missing_backend():
    with patch.dict(os.environ, {"DATA_BACKEND": ""}, clear=True):
        with pytest.raises(RuntimeError, match="explicitly set to 'neo4j'"):
            PointInTimeStore.get_instance()

def test_store_fails_closed_csv_backend():
    with patch.dict(os.environ, {"DATA_BACKEND": "csv"}, clear=True):
        with pytest.raises(RuntimeError, match="explicitly set to 'neo4j'"):
            PointInTimeStore.get_instance()

def test_store_fails_closed_missing_neo4j_uri():
    with patch.dict(os.environ, {"DATA_BACKEND": "neo4j", "NEO4J_URI": ""}, clear=True):
        with pytest.raises(RuntimeError, match="NEO4J_URI is required"):
            PointInTimeStore.get_instance()

@patch("src.inference.neo4j_store.Neo4jPointInTimeStore")
def test_store_initializes_neo4j_successfully(mock_neo4j_store):
    with patch.dict(os.environ, {"DATA_BACKEND": "neo4j", "NEO4J_URI": "bolt://mock:7687", "NEO4J_USER": "test", "NEO4J_PASSWORD": "pwd"}):
        store = PointInTimeStore.get_instance()
        assert store is not None
        mock_neo4j_store.assert_called_once()
