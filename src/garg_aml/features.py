"""
Neighbourhood summary statistics built on top of the GARG-AML score.

For every node: the min/mean/max/std of its neighbours' scores and of their
degrees, plus its own degree. These are the features the paper's tree and
boosting models receive alongside the score itself, and they are what makes the
score usable as an input to a model of your own.

A node with no neighbours returns zero for all eight statistics. That is
deliberate and it is load-bearing -- Louvain reduction strands many nodes, so
the branch is common rather than exotic. See docs/decisions/0003.

Copied unchanged from the research repository, except that the original's bare
``except:`` around the numpy reductions is written here as the explicit empty
check it always was.
"""

import networkx as nx
import numpy as np
import pandas as pd

from .scores import define_gargaml_scores


def summaries_neighbourhoors_node(node, G_copy, measures):
    """Min, mean, max and std of the neighbours' scores."""
    G_ego = nx.ego_graph(G_copy, node)
    G_ego.remove_node(node)
    ego_list = list(G_ego.nodes)

    list_ego_measures = []
    for n in ego_list:
        list_ego_measures.append(measures[n])

    if not list_ego_measures:
        return [0, 0, 0, 0]

    return [
        np.min(list_ego_measures),
        np.mean(list_ego_measures),
        np.max(list_ego_measures),
        np.std(list_ego_measures),
    ]


def degree_neighbours_node(node, G_copy, G_degree_dict):
    """Min, mean, max and std of the neighbours' degrees."""
    G_ego = nx.ego_graph(G_copy, node)
    G_ego.remove_node(node)
    ego_list = list(G_ego.nodes)

    list_ego_degree = []
    for n in ego_list:
        list_ego_degree.append(G_degree_dict[n])

    if not list_ego_degree:
        return [0, 0, 0, 0]

    return [
        np.min(list_ego_degree),
        np.mean(list_ego_degree),
        np.max(list_ego_degree),
        np.std(list_ego_degree),
    ]


def combine_GARG_AML(G_selection, measures_dict, summary_dict, neigh_degree_dict):
    """Assemble scores, neighbour statistics and degrees into one frame."""
    degree_df = pd.DataFrame(dict(G_selection.degree()), index=["degree"]).transpose()

    measures_df = pd.DataFrame(measures_dict, index=["GARGAML"]).transpose()

    summary_df = pd.DataFrame(
        summary_dict,
        index=["GARGAML_min", "GARGAML_mean", "GARGAML_max", "GARGAML_std"],
    ).transpose()

    neigh_degree_df = pd.DataFrame(
        neigh_degree_dict,
        index=["degree_min", "degree_mean", "degree_max", "degree_std"],
    ).transpose()

    GARG_AML_df = (
        measures_df.merge(summary_df, left_index=True, right_index=True)
        .merge(degree_df, left_index=True, right_index=True)
        .merge(neigh_degree_df, left_index=True, right_index=True)
    )

    return GARG_AML_df


def summarise_gargaml_scores(G_reduced, df_results, columns=None):
    """Neighbourhood statistics for a frame of scores."""
    if columns is None:
        columns = ["GARGAML"]

    G_degree_dict = dict(G_reduced.degree())
    nodes = list(df_results.index)

    gargaml_values = dict(zip(df_results.index, df_results["GARGAML"], strict=False))

    summaries_neighbourhood = {}
    summaries_degree = {}

    for node in nodes:
        summaries_neighbourhood[node] = summaries_neighbourhoors_node(
            node, G_reduced, gargaml_values
        )
        summaries_degree[node] = degree_neighbours_node(node, G_reduced, G_degree_dict)

    GARGAML_df = combine_GARG_AML(
        G_reduced, gargaml_values, summaries_neighbourhood, summaries_degree
    )

    return GARGAML_df[columns]


__all__ = [
    "combine_GARG_AML",
    "define_gargaml_scores",
    "degree_neighbours_node",
    "summaries_neighbourhoors_node",
    "summarise_gargaml_scores",
]
