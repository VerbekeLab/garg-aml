"""
The public API: composition, not new arithmetic.

`score` must agree with calling the two stages by hand, or the convenience
layer has become a second implementation -- the thing docs/decisions/0004
exists to prevent.
"""

import networkx as nx
import pandas as pd
import pytest

import garg_aml as ga
from garg_aml.measures import block_measures
from garg_aml.preprocess import reduce_graph
from garg_aml.scores import scores_from_measures

SMURFING = [
    ("a", "m1"),
    ("a", "m2"),
    ("a", "m3"),
    ("m1", "b"),
    ("m2", "b"),
    ("m3", "b"),
]
CLIQUE = [("x", "y"), ("y", "z"), ("z", "x"), ("x", "w"), ("y", "w"), ("z", "w")]


@pytest.fixture
def graph():
    return nx.Graph(SMURFING + CLIQUE)


@pytest.mark.parametrize("directed", [False, True])
def test_score_matches_the_two_stage_path(directed):
    graph = nx.DiGraph(SMURFING) if directed else nx.Graph(SMURFING)

    by_hand = scores_from_measures(ga.block_measures_frame(graph), directed)
    pd.testing.assert_frame_equal(ga.score(graph), by_hand)


def test_direction_is_inferred_from_the_graph():
    edges = nx.DiGraph(SMURFING)
    pd.testing.assert_frame_equal(ga.score(edges), ga.score(edges, directed=True))


def test_reduce_is_the_same_as_reducing_first(graph):
    pd.testing.assert_frame_equal(
        ga.score(graph, reduce=True, resolution=1),
        ga.score(reduce_graph(graph, resolution=1)),
    )


def test_return_measures_appends_the_block_columns(graph):
    plain = ga.score(graph)
    detailed = ga.score(graph, return_measures=True)

    assert list(detailed.columns[: len(plain.columns)]) == list(plain.columns)
    assert "measure_2" in detailed.columns
    assert "size_2" in detailed.columns
    pd.testing.assert_frame_equal(detailed[plain.columns], plain)


def test_block_measures_frame_agrees_with_one_node(graph):
    frame = ga.block_measures_frame(graph).set_index("node")

    for node in ("a", "x"):
        row = frame.loc[node].tolist()
        assert row == pytest.approx(
            list(block_measures(graph, node, include_sizes=True))
        )


def test_score_edges_matches_score(graph):
    edges = pd.DataFrame(SMURFING + CLIQUE, columns=["source", "target"])
    pd.testing.assert_frame_equal(ga.score_edges(edges), ga.score(graph))


def test_score_edges_takes_custom_column_names():
    edges = pd.DataFrame(SMURFING, columns=["from_account", "to_account"])
    scores = ga.score_edges(edges, "from_account", "to_account")
    assert float(scores.loc["a", "GARGAML"]) == 1.0


def test_score_edges_drops_self_loops():
    edges = pd.DataFrame([*SMURFING, ("a", "a")], columns=["source", "target"])
    pd.testing.assert_frame_equal(ga.score_edges(edges), ga.score(nx.Graph(SMURFING)))


@pytest.mark.parametrize(
    "relabel",
    [str, int, lambda n: (n, n)],
    ids=["string", "integer", "tuple"],
)
def test_node_identity_survives(relabel):
    graph = nx.convert_node_labels_to_integers(nx.Graph(SMURFING))
    graph = nx.relabel_nodes(graph, {n: relabel(n) for n in graph})

    scores = ga.score(graph)
    assert set(scores.index) == set(graph.nodes)


def test_parallel_matches_serial(graph):
    pytest.importorskip("joblib")
    pd.testing.assert_frame_equal(ga.score(graph, n_jobs=2), ga.score(graph, n_jobs=1))


def test_unknown_score_type_is_rejected(graph):
    with pytest.raises(ValueError, match="unknown score_type"):
        ga.score(graph, score_type="geometric")


def test_public_api_is_importable():
    missing = [name for name in ga.__all__ if not hasattr(ga, name)]
    assert missing == []


def test_unknown_attribute_still_raises():
    with pytest.raises(AttributeError, match="no attribute"):
        _ = ga.definitely_not_a_function
