"""
Each pipeline stage rebuilt from garg_aml, for comparison against the fixtures.

Mirrors tools/make_golden.py stage for stage. Any divergence between this file
and that one would make the comparison meaningless, so keep them in step.
"""

import networkx as nx
import pandas as pd

from garg_aml.features import summarise_gargaml_scores
from garg_aml.measures import (
    GARG_AML_node_directed_measures,
    GARG_AML_node_undirected_measures,
)
from garg_aml.scores import define_gargaml_scores

SCORE_TYPES = ["basic", "weighted_average"]
FEATURE_SCORE_TYPE = "weighted_average"

FEATURE_COLUMNS = [
    "GARGAML",
    "GARGAML_min",
    "GARGAML_mean",
    "GARGAML_max",
    "GARGAML_std",
    "degree",
    "degree_min",
    "degree_mean",
    "degree_max",
    "degree_std",
]

DIRECTED_COLUMNS = [f"measure_{i}{j}" for i in range(3) for j in range(3)] + [
    f"size_{i}{j}" for i in range(3) for j in range(3)
]
UNDIRECTED_COLUMNS = [
    "measure_1",
    "measure_2",
    "measure_3",
    "size_1",
    "size_2",
    "size_3",
]


def load_graph(edges_path, directed, nodes_path=None):
    """Rebuild a graph from a frozen node list and edge list."""
    G = nx.DiGraph() if directed else nx.Graph()
    if nodes_path is not None:
        G.add_nodes_from(pd.read_csv(nodes_path)["node"])
    data = pd.read_csv(edges_path)
    G.add_edges_from(zip(data["source"], data["target"], strict=True))
    G.remove_edges_from([(n, n) for n in G.nodes() if G.has_edge(n, n)])
    return G


def edge_frame(G):
    """Sorted edge list of a graph."""
    return pd.DataFrame(
        sorted((int(u), int(v)) for u, v in G.edges()), columns=["source", "target"]
    )


def node_frame(G):
    """Sorted node list of a graph."""
    return pd.DataFrame({"node": sorted(G.nodes)})


def measures_frame(G, directed):
    """Stage 1: per-node block measures and block sizes."""
    nodes = sorted(G.nodes)

    if directed:
        G_und = G.to_undirected()
        G_rev = G.reverse(copy=True)
        columns = DIRECTED_COLUMNS
        rows = [
            GARG_AML_node_directed_measures(n, G, G_und, G_rev, include_size=True)
            for n in nodes
        ]
    else:
        columns = UNDIRECTED_COLUMNS
        rows = [
            GARG_AML_node_undirected_measures(n, G, include_size=True) for n in nodes
        ]

    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "node", nodes)
    return frame


def scores_frame(measures, directed):
    """Stage 2a: measures to score, for every score type, side by side."""
    parts = [
        define_gargaml_scores(measures, directed, score_type=score_type).add_prefix(
            score_type + "__"
        )
        for score_type in SCORE_TYPES
    ]
    return pd.concat(parts, axis=1).sort_index()


def features_frame(G, measures, directed):
    """Stage 2b: score plus neighbourhood summary statistics."""
    scores = define_gargaml_scores(measures, directed, score_type=FEATURE_SCORE_TYPE)
    return summarise_gargaml_scores(G, scores, columns=FEATURE_COLUMNS).sort_index()
