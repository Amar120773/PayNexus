"""Point-in-Time Data Access Layer enforcing a Neo4j-only production architecture."""

import pandas as pd
from pathlib import Path
import os
from abc import ABC, abstractmethod
import importlib
from dotenv import load_dotenv

class PointInTimeStore(ABC):
    _instance = None

    @abstractmethod
    def get_network_subgraph(self, merchant_id: str, end_timestamp: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        pass

    @abstractmethod
    def get_merchant(self, merchant_id: str) -> pd.DataFrame:
        pass

    @classmethod
    def get_instance(cls, data_dir: Path | str = "data/synthetic_v2") -> "PointInTimeStore":
        if cls._instance is None:
            # 1. Enforce DATA_BACKEND=neo4j fail-closed logic
            backend = os.getenv("DATA_BACKEND", "")
            if backend.lower() != "neo4j":
                raise RuntimeError(
                    f"CRITICAL: DATA_BACKEND must be explicitly set to 'neo4j'. "
                    f"Received '{backend}'. CSV fallback has been permanently removed from production."
                )

            # 2. Enforce NEO4J_URI fail-closed logic
            load_dotenv()
            if not os.getenv("NEO4J_URI"):
                raise RuntimeError("CRITICAL: NEO4J_URI is required for production inference.")

            try:
                module = importlib.import_module("src.inference.neo4j_store")
                cls._instance = module.Neo4jPointInTimeStore(data_dir)
            except ImportError:
                raise RuntimeError("Neo4j backend requested but neo4j_store module not found.")

        return cls._instance
