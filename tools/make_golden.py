"""
Phase 0 of the packaging migration: freeze the current behaviour as fixtures.

Runs the *current* GARG-AML implementation over a handful of small, fully
reproducible graphs and writes every intermediate to ``golden/``. Those files
become the oracle the extracted ``garg-aml`` package is tested against: if a
refactor changes any number here, the refactor is wrong.

Run from the repository root:

    python scripts/make_golden.py

Design notes
------------
*The edge list is the fixture input, not the generator.* Graphs are built once
with igraph and immediately written to ``edges.csv``; every downstream number is
then computed from the *reloaded* file. The package's tests never need igraph,
a seed, or this script -- they read the edge list and compare.

*Louvain is frozen as an edge list, not re-run.* ``reduced_edges_*.csv`` is both
an output (to test ``reduce_graph``) and an input (the reduced-graph measures
are computed from it). A networkx upgrade that changes the Louvain partition
therefore breaks exactly one test instead of all of them.

*Node order is sorted out.* Every frame is sorted by node before writing, so the
fixtures do not encode dict insertion order.

*Features use ``weighted_average`` only.* That is the documented default and
what every experiment uses; the ``basic`` path is already covered by the score
fixtures.
"""

import json
import os
import platform
import random
import subprocess
import sys

DIR = "./"
os.chdir(DIR)
sys.path.append(DIR)

import networkx as nx
import numpy as np
import pandas as pd

from src.methods.GARGAML import (
    GARG_AML_node_directed_measures,
    GARG_AML_node_undirected_measures,
)
from src.methods.gargaml_scores import define_gargaml_scores, summarise_gargaml_scores
from src.utils.graph_processing import graph_community

GOLDEN_DIR = "golden"
SEED = 1997
RESOLUTION = 10

SCORE_TYPES = ["basic", "weighted_average"]
FEATURE_SCORE_TYPE = "weighted_average"

FEATURE_COLUMNS = [
    "GARGAML",
    "GARGAML_min", "GARGAML_mean", "GARGAML_max", "GARGAML_std",
    "degree",
    "degree_min", "degree_mean", "degree_max", "degree_std",
]


# ---------------------------------------------------------------------------
# Case graphs
# ---------------------------------------------------------------------------

def build_toy():
    """
    The paper's toy example (Figures A1-A6), as built in notebooks/toyexample.ipynb.

    A 20-node Watts-Strogatz ring plus one injected smurfing pattern: node 23
    pays 20, 21 and 22, which all pay 19. Node 23 is the textbook source, 19 the
    textbook target, and neither transacts with the other.
    """
    import igraph as ig

    random.seed(SEED)
    ring = ig.Graph(directed=True).Watts_Strogatz(1, 20, 2, 0.2)

    sources = [e.source for e in ring.es]
    targets = [e.target for e in ring.es]

    sources += [23, 23, 23, 20, 21, 22]
    targets += [20, 21, 22, 19, 19, 19]

    return list(zip(sources, targets))


def build_synthetic(method, n_nodes, m_edges, p_edges, n_patterns):
    """
    One synthetic graph with injected smurfing, using this repo's own generator.

    Mirrors ``create_synthetic_data`` but without its file writes and plots, and
    with the RNG seeded so the run is reproducible.
    """
    import igraph as ig

    from src.data.synthetic_smurfing import add_smurfing_patterns

    random.seed(SEED)

    if method == "Barabasi-Albert":
        rg = ig.Graph().Barabasi(n_nodes, m=m_edges)
    elif method == "Erdos-Renyi":
        rg = ig.Graph().Erdos_Renyi(n_nodes, p=p_edges / 10)
    elif method == "Watts-Strogatz":
        rg = ig.Graph().Watts_Strogatz(1, n_nodes, m_edges, p_edges)
    else:
        raise ValueError("Invalid generation method: " + method)

    list_nodes = rg.vs.indices
    random.shuffle(list_nodes)

    rg.vs["new_node"] = False
    rg.vs["laundering"] = False
    rg.vs["separate"] = False
    rg.vs["new_mules"] = False
    rg.vs["existing_mules"] = False
    rg.es["laundering"] = False

    for pattern in ["separate", "new_mules", "existing_mules"]:
        rg, list_nodes = add_smurfing_patterns(
            rg, n_patterns, list_nodes, type_pattern=pattern
        )
    rg.simplify(combine_edges="max")

    return [(e.source, e.target) for e in rg.es]


CASES = {
    "toy": build_toy,
    "synth_ba": lambda: build_synthetic("Barabasi-Albert", 200, 2, 0, 3),
    "synth_er": lambda: build_synthetic("Erdos-Renyi", 200, 0, 0.01, 3),
    "synth_ws": lambda: build_synthetic("Watts-Strogatz", 200, 2, 0.01, 3),
}


# ---------------------------------------------------------------------------
# Graph loading -- mirrors src/data/graph_construction.py
# ---------------------------------------------------------------------------

def load_graph(edges_path, directed, nodes_path=None):
    """
    Rebuild a graph from a frozen edge list, exactly as the pipeline does.

    ``nodes_path`` restores nodes that carry no edges. Louvain reduction leaves
    plenty of those behind -- ``graph_community`` keeps every node and drops
    only inter-community edges -- and they are not incidental: an isolated node
    is what triggers the frozen D18/D20 edge cases. An edge list alone cannot
    represent them, so any graph that has been through reduction is frozen as a
    node list *and* an edge list.
    """
    G = nx.DiGraph() if directed else nx.Graph()
    if nodes_path is not None:
        G.add_nodes_from(pd.read_csv(nodes_path)["node"])
    data = pd.read_csv(edges_path)
    G.add_edges_from(zip(data["source"], data["target"]))
    G.remove_edges_from([(n, n) for n in G.nodes() if G.has_edge(n, n)])
    return G


def edge_frame(G):
    """Edge list of a graph, sorted, so the fixture is order-independent."""
    edges = sorted((int(u), int(v)) for u, v in G.edges())
    return pd.DataFrame(edges, columns=["source", "target"])


def node_frame(G):
    """Node list of a graph, sorted."""
    return pd.DataFrame({"node": sorted(G.nodes)})


# ---------------------------------------------------------------------------
# The three pipeline stages
# ---------------------------------------------------------------------------

def measures_frame(G, directed):
    """Stage 1: per-node block measures and block sizes."""
    nodes = sorted(G.nodes)

    if directed:
        G_und = G.to_undirected()
        G_rev = G.reverse(copy=True)
        columns = (
            [f"measure_{i}{j}" for i in range(3) for j in range(3)]
            + [f"size_{i}{j}" for i in range(3) for j in range(3)]
        )
        rows = [
            GARG_AML_node_directed_measures(n, G, G_und, G_rev, include_size=True)
            for n in nodes
        ]
    else:
        columns = ["measure_1", "measure_2", "measure_3", "size_1", "size_2", "size_3"]
        rows = [
            GARG_AML_node_undirected_measures(n, G, include_size=True) for n in nodes
        ]

    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "node", nodes)
    return frame


def scores_frame(measures, directed):
    """Stage 2a: measures -> score, for every score type, side by side."""
    parts = []
    for score_type in SCORE_TYPES:
        scores = define_gargaml_scores(measures, directed, score_type=score_type)
        parts.append(scores.add_prefix(score_type + "__"))
    return pd.concat(parts, axis=1).sort_index()


def features_frame(G, measures, directed):
    """Stage 2b: score + neighbourhood summary statistics."""
    scores = define_gargaml_scores(measures, directed, score_type=FEATURE_SCORE_TYPE)
    features = summarise_gargaml_scores(G, scores, columns=FEATURE_COLUMNS)
    return features.sort_index()


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def write(frame, case, name, index):
    path = os.path.join(GOLDEN_DIR, case, name + ".csv")
    frame.to_csv(path, index=index, index_label="node" if index else None)
    print(f"    {path:<58} {len(frame):>5} rows")


def process_case(case, build):
    print(f"\n=== {case} ===")
    case_dir = os.path.join(GOLDEN_DIR, case)
    os.makedirs(case_dir, exist_ok=True)

    edges = build()
    pd.DataFrame(edges, columns=["source", "target"]).to_csv(
        os.path.join(case_dir, "edges.csv"), index=False
    )

    summary = {}
    for directed in [False, True]:
        label = "directed" if directed else "undirected"
        G = load_graph(os.path.join(case_dir, "edges.csv"), directed)
        reduced = graph_community(G, resolution=RESOLUTION)

        write(node_frame(reduced), case, f"reduced_nodes_{label}", index=False)
        write(edge_frame(reduced), case, f"reduced_edges_{label}", index=False)

        # Reload rather than reuse: the downstream fixtures must be exactly what
        # the frozen files reproduce, not what this process happens to hold.
        reduced = load_graph(
            os.path.join(case_dir, f"reduced_edges_{label}.csv"), directed,
            nodes_path=os.path.join(case_dir, f"reduced_nodes_{label}.csv"),
        )

        for variant, graph in [("raw", G), ("reduced", reduced)]:
            measures = measures_frame(graph, directed)
            write(measures, case, f"measures_{label}_{variant}", index=False)
            write(scores_frame(measures, directed), case,
                  f"scores_{label}_{variant}", index=True)
            write(features_frame(graph, measures, directed), case,
                  f"features_{label}_{variant}", index=True)

        summary[label] = {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "reduced_edges": reduced.number_of_edges(),
        }

    return summary


def manifest(summaries):
    """Record exactly what produced these numbers."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit, dirty = None, None

    return {
        "purpose": (
            "Frozen behaviour of GARG-AML before extraction into the garg-aml "
            "package. Never edit these files to make a test pass."
        ),
        "generated_by": "scripts/make_golden.py",
        "source_repo": "B-Deprez/GARG-AML",
        "source_commit": commit,
        "source_tree_dirty": dirty,
        "settings": {
            "seed": SEED,
            "louvain_resolution": RESOLUTION,
            "score_types": SCORE_TYPES,
            "feature_score_type": FEATURE_SCORE_TYPE,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "igraph": __import__("igraph").__version__,
        },
        "cases": summaries,
    }


if __name__ == "__main__":
    os.makedirs(GOLDEN_DIR, exist_ok=True)

    summaries = {case: process_case(case, build) for case, build in CASES.items()}

    with open(os.path.join(GOLDEN_DIR, "MANIFEST.json"), "w") as f:
        json.dump(manifest(summaries), f, indent=2)
        f.write("\n")

    print(f"\nWrote {GOLDEN_DIR}/MANIFEST.json")
