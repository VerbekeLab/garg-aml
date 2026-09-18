"""The optional scikit-learn wrapper."""

import networkx as nx
import pandas as pd
import pytest

import garg_aml as ga
from garg_aml.features import FEATURE_COLUMNS

sklearn = pytest.importorskip("sklearn")

SMURFING = [("a", "m1"), ("a", "m2"), ("m1", "b"), ("m2", "b")]


@pytest.fixture
def graph():
    return nx.Graph(SMURFING)


def test_fit_transform_returns_the_feature_table(graph):
    features = ga.GargAmlScorer().fit_transform(graph)

    assert list(features.columns) == FEATURE_COLUMNS
    assert set(features.index) == set(graph.nodes)


def test_fit_exposes_scores_and_features(graph):
    estimator = ga.GargAmlScorer().fit(graph)

    pd.testing.assert_frame_equal(estimator.scores_, ga.score(graph))
    pd.testing.assert_frame_equal(estimator.features_, estimator.transform(graph))


def test_parameters_round_trip():
    estimator = ga.GargAmlScorer(reduce=True, resolution=3, score_type="basic")
    assert estimator.get_params()["resolution"] == 3

    estimator.set_params(resolution=7)
    assert estimator.get_params()["resolution"] == 7


def test_reduce_flows_through(graph):
    reduced = ga.reduce_graph(graph, resolution=1)
    pd.testing.assert_frame_equal(
        ga.GargAmlScorer(reduce=True, resolution=1).fit(graph).scores_,
        ga.score(reduced),
    )
