"""Tests for graph construction and analysis."""

from __future__ import annotations

import networkx as nx
import pandas as pd
import pytest

from src.data_generation.config import SyntheticDataConfig
from src.data_generation.generators import generate_dataset
from src.graph.build_graph import (
    build_heterogeneous_graph,
    build_projected_merchant_graph,
    compute_graph_statistics,
)


@pytest.fixture
def sample_dataset() -> dict[str, pd.DataFrame]:
    config = SyntheticDataConfig(
        merchants=30,
        transactions=300,
        customers=80,
        devices=50,
        ips=50,
        settlement_accounts=40,
        mule_networks=2,
        period_days=60,
        seed=99,
    )
    return generate_dataset(config)


def test_heterogeneous_graph_construction(sample_dataset: dict[str, pd.DataFrame]) -> None:
    graph = build_heterogeneous_graph(sample_dataset)

    assert isinstance(graph, nx.Graph)
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    # Ensure all merchants exist as nodes
    merchants = sample_dataset["merchants"]["merchant_id"]
    for m in merchants:
        assert f"merchant:{m}" in graph
        assert graph.nodes[f"merchant:{m}"]["node_type"] == "merchant"

    # Ensure edge attributes exist
    for _, _, data in graph.edges(data=True):
        assert "relationship" in data
        assert "weight" in data
        assert data["weight"] >= 1


def test_projected_merchant_graph_nodes_and_edges(sample_dataset: dict[str, pd.DataFrame]) -> None:
    proj_graph = build_projected_merchant_graph(sample_dataset)

    assert isinstance(proj_graph, nx.Graph)
    assert proj_graph.number_of_nodes() == len(sample_dataset["merchants"])

    # Verify edge metadata
    for _, _, data in proj_graph.edges(data=True):
        assert "weight" in data
        assert "reasons" in data
        assert isinstance(data["reasons"], set)
        assert data["weight"] >= 1


def test_compute_graph_statistics_structure(sample_dataset: dict[str, pd.DataFrame]) -> None:
    hetero = build_heterogeneous_graph(sample_dataset)
    proj = build_projected_merchant_graph(sample_dataset)
    stats = compute_graph_statistics(hetero, proj)

    assert "heterogeneous_graph" in stats
    assert "projected_merchant_graph" in stats

    hg_stats = stats["heterogeneous_graph"]
    assert hg_stats["num_nodes"] == hetero.number_of_nodes()
    assert hg_stats["num_edges"] == hetero.number_of_edges()
    assert "merchant" in hg_stats["nodes_by_type"]
    assert "merchant_degree_statistics" in hg_stats

    proj_stats = stats["projected_merchant_graph"]
    assert proj_stats["num_merchants"] == len(sample_dataset["merchants"])
    assert "density" in proj_stats
    assert "connected_components_count" in proj_stats
