"""
Neighbourhood summary statistics built on top of the GARG-AML score.

For every node: the min, mean, max and standard deviation of its neighbours'
scores and of their degrees, plus its own degree. These are the features the
paper's tree and boosting models receive alongside the score itself, and they
are what makes the score usable as an input to a model of your own.

A node with no neighbours returns zero for all eight statistics. That is
deliberate, and it is common rather than exotic: Louvain reduction strands many
nodes. See ``docs/decisions/0003``.
"""

from collections.abc import Hashable, Mapping, Sequence

import networkx as nx
import numpy as np
import pandas as pd

__all__ = [
    "FEATURE_COLUMNS",
    "build_features",
    "neighbour_degree_stats",
    "neighbour_score_stats",
]

#: Every column :func:`build_features` can return, in order.
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

_EMPTY_STATS = [0, 0, 0, 0]


def _stats(values: list) -> list:
    """Min, mean, max and std, or zeros when there is nothing to summarise."""
    if not values:
        return list(_EMPTY_STATS)
    return [np.min(values), np.mean(values), np.max(values), np.std(values)]


def _neighbours(graph: nx.Graph, node: Hashable) -> list:
    ego = nx.ego_graph(graph, node)
    ego.remove_node(node)
    return list(ego.nodes)


def neighbour_score_stats(graph: nx.Graph, node: Hashable, scores: Mapping) -> list:
    """
    Min, mean, max and standard deviation of the neighbours' scores.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The graph the scores were computed on.
    node : hashable
        The node whose neighbourhood to summarise.
    scores : mapping
        Score per node. Must cover every neighbour of ``node``.

    Returns
    -------
    list
        ``[min, mean, max, std]``, or ``[0, 0, 0, 0]`` when ``node`` has no
        neighbours.

    Examples
    --------
    >>> import networkx as nx
    >>> graph = nx.Graph([("a", "b"), ("a", "c")])
    >>> [float(v) for v in neighbour_score_stats(graph, "a", {"b": 0.0, "c": 1.0})]
    [0.0, 0.5, 1.0, 0.5]
    """
    return _stats([scores[n] for n in _neighbours(graph, node)])


def neighbour_degree_stats(graph: nx.Graph, node: Hashable, degrees: Mapping) -> list:
    """
    Min, mean, max and standard deviation of the neighbours' degrees.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The graph the degrees were taken from.
    node : hashable
        The node whose neighbourhood to summarise.
    degrees : mapping
        Degree per node, as ``dict(graph.degree())`` gives it.

    Returns
    -------
    list
        ``[min, mean, max, std]``, or ``[0, 0, 0, 0]`` when ``node`` has no
        neighbours.

    Examples
    --------
    >>> import networkx as nx
    >>> graph = nx.Graph([("a", "b"), ("a", "c"), ("c", "d")])
    >>> [float(v) for v in neighbour_degree_stats(graph, "a", dict(graph.degree()))]
    [1.0, 1.5, 2.0, 0.5]
    """
    return _stats([degrees[n] for n in _neighbours(graph, node)])


def _assemble(
    graph: nx.Graph, scores: Mapping, score_stats: Mapping, degree_stats: Mapping
) -> pd.DataFrame:
    """Join scores, neighbour statistics and degrees into one frame."""
    frames = [
        pd.DataFrame(scores, index=["GARGAML"]).transpose(),
        pd.DataFrame(
            score_stats,
            index=["GARGAML_min", "GARGAML_mean", "GARGAML_max", "GARGAML_std"],
        ).transpose(),
        pd.DataFrame(dict(graph.degree()), index=["degree"]).transpose(),
        pd.DataFrame(
            degree_stats,
            index=["degree_min", "degree_mean", "degree_max", "degree_std"],
        ).transpose(),
    ]

    assembled = frames[0]
    for frame in frames[1:]:
        assembled = assembled.merge(frame, left_index=True, right_index=True)
    return assembled


def build_features(
    graph: nx.Graph, scores: pd.DataFrame, columns: Sequence[str] | None = None
) -> pd.DataFrame:
    """
    Neighbourhood features for every scored node.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The graph the scores were computed on -- the *reduced* graph, if the
        scores came from one, since the neighbourhoods must match.
    scores : pandas.DataFrame
        Indexed by node, with a ``GARGAML`` column, as
        :func:`garg_aml.scores.scores_from_measures` returns.
    columns : sequence of str, optional
        Which of :data:`FEATURE_COLUMNS` to return. All of them by default.

    Returns
    -------
    pandas.DataFrame
        Indexed by node, one column per requested feature.

    Notes
    -----
    Degrees are taken from ``graph``, so on a Louvain-reduced graph they are
    intra-community degrees, not raw transaction counts.

    Examples
    --------
    >>> import networkx as nx
    >>> import pandas as pd
    >>> graph = nx.Graph([("a", "m1"), ("a", "m2"), ("m1", "b"), ("m2", "b")])
    >>> scores = pd.DataFrame({"GARGAML": [1.0, -0.5, -0.5, 1.0]},
    ...                       index=["a", "m1", "m2", "b"])
    >>> features = build_features(graph, scores, columns=["degree", "GARGAML_mean"])
    >>> [float(v) for v in features.loc["a"]]
    [2.0, -0.5]
    """
    if columns is None:
        columns = FEATURE_COLUMNS

    degrees = dict(graph.degree())
    score_map = dict(zip(scores.index, scores["GARGAML"], strict=True))

    score_stats = {}
    degree_stats = {}
    for node in scores.index:
        score_stats[node] = neighbour_score_stats(graph, node, score_map)
        degree_stats[node] = neighbour_degree_stats(graph, node, degrees)

    return _assemble(graph, score_map, score_stats, degree_stats)[list(columns)]
