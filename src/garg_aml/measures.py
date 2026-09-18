"""
Per-node block measures: the expensive first stage of GARG-AML.

For one node, build its second-order ego graph, order the nodes into blocks and
take each block's density over its free entries. Three blocks undirected, nine
directed.

This stage is deliberately separate from scoring. The measures are what is worth
persisting, and any score variant is a cheap re-aggregation of them -- see
docs/decisions/0004.
"""

from collections.abc import Hashable

import networkx as nx

from ._blocks import (
    _block_00,
    _block_01,
    _block_02,
    _block_1,
    _block_2,
    _block_3,
    _block_10,
    _block_11,
    _block_12,
    _block_20,
    _block_21,
    _block_22,
)
from ._ordering import node_order

__all__ = ["DIRECTED_COLUMNS", "UNDIRECTED_COLUMNS", "block_measures"]

#: Column names for the three undirected blocks, in the order
#: :func:`block_measures` returns them with ``include_sizes=True``.
UNDIRECTED_COLUMNS = [
    "measure_1",
    "measure_2",
    "measure_3",
    "size_1",
    "size_2",
    "size_3",
]

#: Column names for the nine directed blocks, row-major.
DIRECTED_COLUMNS = [f"measure_{i}{j}" for i in range(3) for j in range(3)] + [
    f"size_{i}{j}" for i in range(3) for j in range(3)
]


def _undirected_measures(
    graph: nx.Graph, node: Hashable, include_sizes: bool
) -> tuple[float, ...]:
    """Three block densities for one node of an undirected graph."""
    ego = nx.ego_graph(graph, node, 2)

    first, second, ordered = node_order(ego, node, directed=False)

    adjacency = nx.adjacency_matrix(ego, nodelist=ordered).toarray()

    n_second = len(second)
    n_first = len(first)

    dim_1 = [n_second + 1, n_second + 1]
    dim_2 = [n_first, n_second + 1]
    dim_3 = [n_first, n_first]

    measure_1, size_1 = _block_1(dim_1, adjacency)
    measure_2, size_2 = _block_2(dim_1, dim_2, adjacency)
    measure_3, size_3 = _block_3(dim_1, dim_2, dim_3, adjacency)

    if include_sizes:
        return (measure_1, measure_2, measure_3, size_1, size_2, size_3)
    return (measure_1, measure_2, measure_3)


def _directed_measures(
    graph: nx.DiGraph,
    node: Hashable,
    undirected: nx.Graph,
    reverse: nx.DiGraph,
    include_sizes: bool,
) -> tuple[float, ...]:
    """Nine block densities for one node of a directed graph."""
    # The neighbourhood is taken on the undirected view, so that a node is a
    # neighbour regardless of which way its edges point; the levels are then
    # assigned from the directed and reversed views.
    ego_undirected = nx.ego_graph(undirected, node, 2)
    ego = nx.subgraph(graph, ego_undirected.nodes)
    ego_reverse = nx.ego_graph(reverse, node, 2)

    level_0, level_1, level_2, ordered = node_order(
        ego, node, directed=True, ego_undirected=ego_undirected, ego_reverse=ego_reverse
    )

    adjacency = nx.adjacency_matrix(ego, nodelist=ordered).toarray()

    size_0 = len(level_0)
    size_1 = len(level_1)
    size_2 = len(level_2)

    measure_00, block_00 = _block_00(adjacency, size_0)
    measure_01, block_01 = _block_01(adjacency, size_0, size_1)
    measure_02, block_02 = _block_02(adjacency, size_0, size_1, size_2)
    measure_10, block_10 = _block_10(adjacency, size_0, size_1)
    measure_11, block_11 = _block_11(adjacency, size_0, size_1)
    measure_12, block_12 = _block_12(adjacency, size_0, size_1, size_2)
    measure_20, block_20 = _block_20(adjacency, size_0, size_1, size_2)
    measure_21, block_21 = _block_21(adjacency, size_0, size_1)
    measure_22, block_22 = _block_22(adjacency, size_0, size_1, size_2)

    measures = (
        measure_00,
        measure_01,
        measure_02,
        measure_10,
        measure_11,
        measure_12,
        measure_20,
        measure_21,
        measure_22,
    )
    if include_sizes:
        return (
            *measures,
            block_00,
            block_01,
            block_02,
            block_10,
            block_11,
            block_12,
            block_20,
            block_21,
            block_22,
        )
    return measures


def block_measures(
    graph: nx.Graph,
    node: Hashable,
    directed: bool = False,
    *,
    undirected: nx.Graph | None = None,
    reverse: nx.DiGraph | None = None,
    include_sizes: bool = False,
) -> tuple[float, ...]:
    """
    Block densities of one node's second-order neighbourhood.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The transaction graph. Usually reduced first with
        :func:`garg_aml.preprocess.reduce_graph`.
    node : hashable
        The node to measure. Must be in ``graph``.
    directed : bool, default False
        Use the nine-block directed analysis rather than the three-block
        undirected one.
    undirected, reverse : networkx.Graph, optional
        Precomputed ``graph.to_undirected()`` and ``graph.reverse()``, used only
        when ``directed`` is True. Scoring many nodes of one graph is much
        faster if these are built once and passed in; they are derived on demand
        when omitted.
    include_sizes : bool, default False
        Also return each block's number of free entries, which is what the
        ``weighted_average`` score type weights by.

    Returns
    -------
    tuple of float
        Three densities undirected, nine directed, in row-major block order.
        With ``include_sizes``, the matching free-entry counts follow.

    Notes
    -----
    A block with no free entries does not yield a missing value: the
    off-diagonal blocks fall back to 1 and the rest to 0. Those constants are
    frozen behaviour -- see ``docs/decisions/0003``.

    References
    ----------
    Deprez et al. (2025), sections 3.2 and 3.3.

    Examples
    --------
    One source paying two mules, which both pay one target -- a pure smurfing
    pattern, so the off-diagonal block is full and the others are empty.

    >>> import networkx as nx
    >>> graph = nx.Graph([("a", "m1"), ("a", "m2"), ("m1", "b"), ("m2", "b")])
    >>> [round(float(m), 3) for m in block_measures(graph, "a")]
    [0.0, 1.0, 0.0]
    """
    if not directed:
        return _undirected_measures(graph, node, include_sizes)

    if undirected is None:
        undirected = graph.to_undirected()
    if reverse is None:
        reverse = graph.reverse(copy=True)

    return _directed_measures(graph, node, undirected, reverse, include_sizes)
