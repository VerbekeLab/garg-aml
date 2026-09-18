"""
Ordering of a second-order ego graph's nodes into its analysis blocks.

The block structure GARG-AML measures only appears under a specific node order.
Undirected (section 3.2): ``[ego, second-order neighbours, first-order
neighbours]``. Directed (section 3.3): ``[level 0, level 1, level 2]``, where a
node at distance two sits at level 0 when no directed path of length two reaches
it in either direction -- Eq. (11) applied to the graph and to its reverse.

Copied unchanged from the research repository.
"""

import networkx as nx


def GARG_AML_nodeselection_undirected(G_ego_second, node):
    """Order as ego, second-order neighbours, first-order neighbours."""
    nodes_1 = list(nx.ego_graph(G_ego_second, node).nodes)
    nodes_1.remove(node)
    nodes_2 = list(G_ego_second.nodes)
    nodes_2.remove(node)
    for n in nodes_1:
        nodes_2.remove(n)

    # For undirected networks, specific order to obtain scores
    # (group node with second order neighbours)
    nodes_ordered = [node] + nodes_2 + nodes_1

    return nodes_1, nodes_2, nodes_ordered


def GARG_AML_nodeselection_directed(
    G_ego_second, G_ego_second_und, G_ego_second_rev, node
):
    """Order by level: senders, mules, receivers."""
    nodes_1 = list(nx.ego_graph(G_ego_second_und, node).nodes)
    nodes_1.remove(node)
    nodes_2 = list(G_ego_second.nodes)

    nodes_2_s = list(nx.ego_graph(G_ego_second, node, radius=2).nodes)

    nodes_2_rs = list(nx.ego_graph(G_ego_second_rev, node, radius=2).nodes)

    nodes_0 = list(
        set(nodes_2)
        .difference(set(nodes_2_s))
        .difference(set(nodes_2_rs))
        .difference(set(nodes_1))
    )

    nodes_0 = [node] + nodes_0

    for n in nodes_0:
        nodes_2.remove(n)
    for n in nodes_1:
        nodes_2.remove(n)

    # For directed network, specific order to obtain scores (in order of "group")
    nodes_ordered = nodes_0 + nodes_1 + nodes_2

    return nodes_0, nodes_1, nodes_2, nodes_ordered


def GARG_AML_nodeselection(
    G_ego_second, node, directed, G_ego_second_und=None, G_ego_second_rev=None
):
    """Dispatch to the directed or undirected ordering."""
    if directed:
        return GARG_AML_nodeselection_directed(
            G_ego_second, G_ego_second_und, G_ego_second_rev, node
        )
    else:
        return GARG_AML_nodeselection_undirected(G_ego_second, node)
