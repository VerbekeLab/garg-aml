"""The generator that makes the documentation runnable without a data download."""

import networkx as nx
import pytest

from garg_aml.synthetic import MODELS, smurfing_graph


@pytest.mark.parametrize("model", MODELS)
def test_every_model_builds(model):
    graph, labels = smurfing_graph(n_nodes=60, model=model, n_patterns=1, seed=2)

    assert graph.number_of_nodes() == len(labels)
    assert set(labels.index) == set(graph.nodes)
    assert labels.sum() > 0


def test_generation_is_reproducible():
    first, first_labels = smurfing_graph(n_nodes=80, seed=7)
    second, second_labels = smurfing_graph(n_nodes=80, seed=7)

    assert sorted(map(str, first.edges)) == sorted(map(str, second.edges))
    assert first_labels.equals(second_labels)


def test_different_seeds_differ():
    first, _ = smurfing_graph(n_nodes=80, seed=7)
    second, _ = smurfing_graph(n_nodes=80, seed=8)
    assert sorted(map(str, first.edges)) != sorted(map(str, second.edges))


def test_mules_route_between_source_and_target_without_a_direct_edge():
    graph, _labels = smurfing_graph(n_nodes=60, n_patterns=1, mules=(3, 3), seed=5)

    mules = [n for n in graph.nodes if str(n).startswith("mule_")]
    assert len(mules) == 3

    # Every mule has exactly the source and the target as neighbours, and those
    # two do not transact directly -- that is the pattern being injected.
    endpoints = {frozenset(graph.neighbors(m)) for m in mules}
    assert len(endpoints) == 1
    source, target = endpoints.pop()
    assert not graph.has_edge(source, target)


def test_directed_orients_source_to_mule_to_target():
    graph, _ = smurfing_graph(
        n_nodes=60, n_patterns=1, mules=(2, 2), directed=True, seed=5
    )

    assert isinstance(graph, nx.DiGraph)
    for mule in (n for n in graph.nodes if str(n).startswith("mule_")):
        assert graph.in_degree(mule) == 1
        assert graph.out_degree(mule) == 1


def test_unknown_model_is_rejected():
    with pytest.raises(ValueError, match="unknown model"):
        smurfing_graph(model="preferential-attachment")


def test_graph_too_small_for_the_patterns_is_rejected():
    with pytest.raises(ValueError, match="distinct accounts"):
        smurfing_graph(n_nodes=4, n_patterns=5)
