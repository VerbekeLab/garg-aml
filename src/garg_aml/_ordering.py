"""
Ordering of a second-order ego graph's nodes into its analysis blocks.

The block structure GARG-AML measures only appears under a specific node order.
Undirected (paper section 3.2): ``[ego, second-order neighbours, first-order
neighbours]``. Directed (section 3.3): ``[level 0, level 1, level 2]``, where a
node at distance two sits at level 0 when no directed path of length two reaches
it in either direction -- Eq. (11) applied to the graph and to its reverse.
"""

from collections.abc import Hashable

import networkx as nx


def _undirected_order(ego: nx.Graph, node: Hashable) -> tuple[list, list, list]:
    """Order as ego, second-order neighbours, first-order neighbours."""
    first = list(nx.ego_graph(ego, node).nodes)
    first.remove(node)
    second = list(ego.nodes)
    second.remove(node)
    for n in first:
        second.remove(n)

    # The ego node is grouped with its second-order neighbours: that is the
    # partition whose on-diagonal blocks a smurfing pattern leaves empty.
    return first, second, [node, *second, *first]


def _directed_order(
    ego: nx.DiGraph, ego_undirected: nx.Graph, ego_reverse: nx.DiGraph, node: Hashable
) -> tuple[list, list, list, list]:
    """Order by level: senders, mules, receivers."""
    level_1 = list(nx.ego_graph(ego_undirected, node).nodes)
    level_1.remove(node)
    level_2 = list(ego.nodes)

    reachable = list(nx.ego_graph(ego, node, radius=2).nodes)
    reaching = list(nx.ego_graph(ego_reverse, node, radius=2).nodes)

    # Eq. (11): a node at distance two with no directed path of length two in
    # either direction is a sender.
    level_0 = list(
        set(level_2)
        .difference(set(reachable))
        .difference(set(reaching))
        .difference(set(level_1))
    )

    level_0 = [node, *level_0]

    for n in level_0:
        level_2.remove(n)
    for n in level_1:
        level_2.remove(n)

    return level_0, level_1, level_2, level_0 + level_1 + level_2


def node_order(
    ego: nx.Graph,
    node: Hashable,
    directed: bool,
    ego_undirected: nx.Graph | None = None,
    ego_reverse: nx.DiGraph | None = None,
) -> tuple:
    """Dispatch to the directed or undirected ordering."""
    if directed:
        return _directed_order(ego, ego_undirected, ego_reverse, node)
    return _undirected_order(ego, node)
