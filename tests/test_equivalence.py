"""
The L2 test: the extracted code must agree with the implementation it came from.

Where test_golden.py pins four fixed graphs, this sweeps a spread of shapes --
including the degenerate ones no real dataset would contain -- and compares the
new implementation against the old one node by node.

It needs the research repository beside this one, so it skips in CI. Set
GARGAML_RESEARCH_REPO to point elsewhere.

**This file is deleted at Phase 5.** Its job is to prove the extraction, and
keeping a dependency on the old tree afterwards is the coupling the migration
exists to remove.
"""

import os
import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

from garg_aml.preprocess import graph_community

from ._pipeline import features_frame, measures_frame, scores_frame

RESEARCH_REPO = Path(
    os.environ.get("GARGAML_RESEARCH_REPO", Path(__file__).parents[3] / "GARG-AML")
)

pytestmark = pytest.mark.skipif(
    not (RESEARCH_REPO / "src" / "methods" / "GARGAML.py").exists(),
    reason=f"research repository not found at {RESEARCH_REPO}",
)


def _old():
    """Import the pre-extraction implementation."""
    if str(RESEARCH_REPO) not in sys.path:
        sys.path.insert(0, str(RESEARCH_REPO))

    from src.methods.GARGAML import (
        GARG_AML_node_directed_measures,
        GARG_AML_node_undirected_measures,
    )
    from src.methods.gargaml_scores import (
        define_gargaml_scores,
        summarise_gargaml_scores,
    )
    from src.methods.utils.neighbourhood_functions import GARG_AML_nodeselection
    from src.utils.graph_processing import graph_community as old_community

    return {
        "undirected_measures": GARG_AML_node_undirected_measures,
        "directed_measures": GARG_AML_node_directed_measures,
        "nodeselection": GARG_AML_nodeselection,
        "scores": define_gargaml_scores,
        "summarise": summarise_gargaml_scores,
        "community": old_community,
    }


def _smurfing_edges(n_mules):
    """One source paying n mules, which all pay one target."""
    source, target = "source", "target"
    mules = [f"mule_{i}" for i in range(n_mules)]
    return [(source, m) for m in mules] + [(m, target) for m in mules]


# Shapes chosen to exercise the degenerate paths as hard as the ordinary ones:
# empty and single-node graphs, isolated nodes, a clique (no block structure at
# all), and a perfect smurfing pattern (maximal block structure).
GRAPH_SPECS = {
    "empty": nx.empty_graph(0),
    "single_node": nx.empty_graph(1),
    "isolated_pair": nx.empty_graph(2),
    "one_edge": nx.path_graph(2),
    "star_8": nx.star_graph(8),
    "clique_6": nx.complete_graph(6),
    "path_7": nx.path_graph(7),
    "cycle_7": nx.cycle_graph(7),
    "smurf_3": nx.Graph(_smurfing_edges(3)),
    "smurf_8": nx.Graph(_smurfing_edges(8)),
    "two_components": nx.disjoint_union(nx.star_graph(4), nx.complete_graph(4)),
    **{f"ba_50_{s}": nx.barabasi_albert_graph(50, 2, seed=s) for s in (1, 2, 3)},
    **{f"er_50_{s}": nx.erdos_renyi_graph(50, 0.08, seed=s) for s in (1, 2, 3)},
    **{f"ws_50_{s}": nx.watts_strogatz_graph(50, 4, 0.1, seed=s) for s in (1, 2, 3)},
}

CASES = sorted(GRAPH_SPECS)


def _build(name, directed):
    """Same edge set as a Graph or a DiGraph, with node labels normalised."""
    source = GRAPH_SPECS[name]
    G = nx.DiGraph() if directed else nx.Graph()
    G.add_nodes_from(source.nodes)
    G.add_edges_from(source.edges)
    return G


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("directed", [False, True], ids=["undirected", "directed"])
def test_node_ordering_matches(name, directed):
    old = _old()
    G = _build(name, directed)

    for node in sorted(G.nodes, key=str):
        if directed:
            ego_und = nx.ego_graph(G.to_undirected(), node, 2)
            ego = nx.subgraph(G, ego_und.nodes)
            ego_rev = nx.ego_graph(G.reverse(copy=True), node, 2)
            expected = old["nodeselection"](
                ego, node, True, G_ego_second_und=ego_und, G_ego_second_rev=ego_rev
            )
            from garg_aml._ordering import GARG_AML_nodeselection

            produced = GARG_AML_nodeselection(
                ego, node, True, G_ego_second_und=ego_und, G_ego_second_rev=ego_rev
            )
        else:
            ego = nx.ego_graph(G, node, 2)
            expected = old["nodeselection"](ego, node, False)

            from garg_aml._ordering import GARG_AML_nodeselection

            produced = GARG_AML_nodeselection(ego, node, False)

        assert produced == expected, f"ordering differs at node {node}"


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("directed", [False, True], ids=["undirected", "directed"])
def test_block_measures_match(name, directed):
    old = _old()
    G = _build(name, directed)

    if directed:
        G_und, G_rev = G.to_undirected(), G.reverse(copy=True)

    for node in sorted(G.nodes, key=str):
        if directed:
            expected = old["directed_measures"](
                node, G, G_und, G_rev, include_size=True
            )
        else:
            expected = old["undirected_measures"](node, G, include_size=True)

        produced = measures_frame(G, directed)
        row = produced[produced["node"] == node].iloc[0].drop("node").tolist()

        assert row == pytest.approx(list(expected), rel=0, abs=0), (
            f"measures differ at node {node}"
        )


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("directed", [False, True], ids=["undirected", "directed"])
def test_scores_and_features_match(name, directed):
    old = _old()
    G = _build(name, directed)
    if G.number_of_nodes() == 0:
        pytest.skip("no nodes to score")

    measures = measures_frame(G, directed)

    for score_type in ("basic", "weighted_average"):
        expected = old["scores"](measures, directed, score_type=score_type)
        produced = scores_frame(measures, directed)
        for column in expected.columns:
            pd.testing.assert_series_equal(
                produced[f"{score_type}__{column}"].rename(column),
                expected[column].sort_index(),
                rtol=0,
            )

    expected_features = old["summarise"](
        G,
        old["scores"](measures, directed, score_type="weighted_average"),
        columns=[
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
        ],
    ).sort_index()
    pd.testing.assert_frame_equal(
        features_frame(G, measures, directed), expected_features, rtol=0
    )


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("directed", [False, True], ids=["undirected", "directed"])
def test_louvain_reduction_matches(name, directed):
    old = _old()
    G = _build(name, directed)

    produced = graph_community(G, resolution=10)
    expected = old["community"](G, resolution=10)

    assert sorted(produced.nodes, key=str) == sorted(expected.nodes, key=str)
    assert sorted(map(str, produced.edges)) == sorted(map(str, expected.edges))
