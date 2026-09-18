"""
Each pipeline stage rebuilt from garg_aml, for comparison against the fixtures.

Mirrors tools/make_golden.py stage for stage. Any divergence between this file
and that one would make the comparison meaningless, so keep them in step.
"""

import numbers

import networkx as nx
import pandas as pd

from garg_aml.features import build_features
from garg_aml.measures import block_measures
from garg_aml.scores import scores_from_measures

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


def index_values(frame):
    """
    A frame's index as comparable values, ignoring numeric dtype.

    The old directed path collected node ids through DataFrame.iterrows(),
    which cast integer ids to float; the package preserves them. Comparing
    numeric ids as floats lets both test layers check that the right nodes are
    present and aligned without demanding the old artefact. Non-numeric ids --
    the string account names of the smurfing fixtures -- compare as themselves.
    See docs/decisions/0008.
    """
    return [float(i) if isinstance(i, numbers.Number) else i for i in frame.index]


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
            block_measures(
                G, n, directed=True, undirected=G_und, reverse=G_rev, include_sizes=True
            )
            for n in nodes
        ]
    else:
        columns = UNDIRECTED_COLUMNS
        rows = [block_measures(G, n, include_sizes=True) for n in nodes]

    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "node", nodes)
    return frame


def scores_frame(measures, directed):
    """Stage 2a: measures to score, for every score type, side by side."""
    parts = [
        scores_from_measures(measures, directed, score_type=score_type).add_prefix(
            score_type + "__"
        )
        for score_type in SCORE_TYPES
    ]
    return pd.concat(parts, axis=1).sort_index()


def features_frame(G, measures, directed):
    """Stage 2b: score plus neighbourhood summary statistics."""
    scores = scores_from_measures(measures, directed, score_type=FEATURE_SCORE_TYPE)
    return build_features(G, scores, columns=FEATURE_COLUMNS).sort_index()
