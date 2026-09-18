"""
Optional graph preprocessing applied before scoring.

``graph_community`` partitions the graph with Louvain and keeps only
intra-community edges (paper Algorithm 1). It is **lossy**: on the IBM data it
removes the large majority of edges, and it changes which neighbourhoods exist
at all. That is why it stays a separate, explicit step rather than something
``score`` does behind the caller's back -- see docs/decisions/0002.

``graph_degree`` removes the highest-degree nodes, which is not part of the
published pipeline but is useful on graphs with hubs.

Copied unchanged from the research repository.
"""

import networkx as nx
import pandas as pd


def graph_degree(G, degree_cutoff=0.01):
    """Remove the top ``degree_cutoff`` quantile of nodes by degree."""
    # Delete the hubs
    # The cut-off is defined as a relative number
    G_copy = G.copy()

    degree_df = pd.DataFrame(dict(G_copy.degree()), index=["Degree"]).transpose()

    degree_threshold = degree_df["Degree"].quantile(1 - degree_cutoff)
    hub_criteria = degree_df["Degree"] >= degree_threshold

    hubs_deleted = list(degree_df[hub_criteria].reset_index()["index"])

    G_copy.remove_nodes_from(hubs_deleted)

    return G_copy


def graph_community(G, resolution=10):
    """Keep only intra-community edges of a Louvain partition."""
    # large resolution to have smaller communities
    directed = nx.is_directed(G)

    if directed:
        G_undirected = G.copy().to_undirected()
    else:
        G_undirected = G.copy()

    community_list = nx.community.louvain_communities(
        G_undirected, resolution=resolution, seed=1997
    )

    # Create a dictionary to map nodes to their community
    node_community = {}
    for idx, community in enumerate(community_list):
        for node in community:
            node_community[node] = idx

    # Create a new graph with only intra-community edges
    if directed:
        H = nx.DiGraph()
    else:
        H = nx.Graph()

    H.add_nodes_from(G.nodes(data=True))  # Add all nodes with their attributes

    # Add only edges that connect nodes within the same community
    for u, v in G.edges():
        if node_community[u] == node_community[v]:
            H.add_edge(u, v, **G[u][v])

    return H
