"""
Optional graph preprocessing applied before scoring.

:func:`reduce_graph` partitions the graph with Louvain and keeps only
intra-community edges (paper Algorithm 1). It is **lossy** -- on the IBM data it
removes the large majority of edges, and it changes which neighbourhoods exist
at all. That is why it is a separate, explicit step rather than something
scoring does behind the caller's back; see ``docs/decisions/0002``.

:func:`drop_hubs` removes the highest-degree nodes. It is not part of the
published pipeline, but it is useful on graphs with heavy hubs.
"""

import networkx as nx
import pandas as pd

__all__ = ["drop_hubs", "reduce_graph"]

#: The seed used throughout the paper.
SEED = 1997


def drop_hubs(graph: nx.Graph, quantile: float = 0.01) -> nx.Graph:
    """
    Remove the highest-degree nodes.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The graph to prune. It is not modified.
    quantile : float, default 0.01
        Fraction of nodes to treat as hubs. Every node whose degree is at or
        above the ``1 - quantile`` degree quantile is removed, so ties at the
        threshold can push the number removed above the nominal fraction.

    Returns
    -------
    networkx.Graph
        A copy without the hub nodes or their edges.

    Examples
    --------
    >>> import networkx as nx
    >>> graph = nx.barabasi_albert_graph(30, 2, seed=1)
    >>> drop_hubs(graph, quantile=0.1).number_of_nodes()
    27
    """
    pruned = graph.copy()

    degrees = pd.DataFrame(dict(pruned.degree()), index=["degree"]).transpose()

    threshold = degrees["degree"].quantile(1 - quantile)
    hubs = list(degrees[degrees["degree"] >= threshold].reset_index()["index"])

    pruned.remove_nodes_from(hubs)

    return pruned


def reduce_graph(graph: nx.Graph, resolution: float = 10, seed: int = SEED) -> nx.Graph:
    """
    Keep only the intra-community edges of a Louvain partition.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The transaction graph. It is not modified, and a directed graph stays
        directed: the partition is found on the undirected view, but the edges
        that survive keep their direction.
    resolution : float, default 10
        Louvain resolution. Higher values give smaller communities and so cut
        more edges. The published results use 10.
    seed : int, default 1997
        Seed for the Louvain partition, which is otherwise not deterministic.

    Returns
    -------
    networkx.Graph
        A graph with every node of the input but only the edges whose endpoints
        share a community. Node and edge attributes are preserved.

    Notes
    -----
    This step is lossy by design, and nodes that lose all their edges are kept
    rather than dropped -- they go on to score -1. See ``docs/decisions/0002``
    and ``docs/decisions/0003``.

    References
    ----------
    Deprez et al. (2025), Algorithm 1.

    Examples
    --------
    Two cliques joined by a single edge. At resolution 1 the bridge is cut and
    both cliques survive intact:

    >>> import networkx as nx
    >>> graph = nx.disjoint_union(nx.complete_graph(4), nx.complete_graph(4))
    >>> graph.add_edge(0, 4)
    >>> reduce_graph(graph, resolution=1).number_of_edges()
    12

    At the published resolution of 10 the communities are smaller than a clique,
    so every edge goes and all eight nodes are left isolated. Nothing is dropped
    -- they simply have no neighbourhood left to score:

    >>> reduce_graph(graph).number_of_edges()
    0
    >>> reduce_graph(graph).number_of_nodes()
    8
    """
    directed = nx.is_directed(graph)

    undirected = graph.to_undirected() if directed else graph.copy()

    communities = nx.community.louvain_communities(
        undirected, resolution=resolution, seed=seed
    )

    membership = {}
    for index, community in enumerate(communities):
        for node in community:
            membership[node] = index

    reduced = nx.DiGraph() if directed else nx.Graph()
    reduced.add_nodes_from(graph.nodes(data=True))

    for u, v in graph.edges():
        if membership[u] == membership[v]:
            reduced.add_edge(u, v, **graph[u][v])

    return reduced
