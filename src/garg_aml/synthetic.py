"""
Synthetic transaction graphs with known smurfing patterns.

For documentation examples and tests: it needs no data download, and the ground
truth is known, so an example can show that the score actually separates the
injected pattern from the background.

It does **not** reproduce the synthetic datasets used in the paper. Those were
generated with python-igraph under its own RNG; reproducing them bit for bit
would mean a second core dependency for no user-facing gain. Use the research
repository's generator for that. See ``docs/decisions/0005``.
"""

import random
from collections.abc import Hashable

import networkx as nx
import pandas as pd

__all__ = ["MODELS", "smurfing_graph"]

#: Background models, and the networkx generator each one uses.
MODELS = ("barabasi-albert", "erdos-renyi", "watts-strogatz")

SEED = 1997


def _background(model: str, n_nodes: int, seed: int) -> nx.Graph:
    if model == "barabasi-albert":
        return nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    if model == "erdos-renyi":
        return nx.erdos_renyi_graph(n_nodes, 0.02, seed=seed)
    if model == "watts-strogatz":
        return nx.watts_strogatz_graph(n_nodes, 4, 0.1, seed=seed)
    raise ValueError(f"unknown model {model!r}; expected one of {MODELS}")


def smurfing_graph(
    n_nodes: int = 200,
    *,
    model: str = "barabasi-albert",
    n_patterns: int = 3,
    mules: tuple[int, int] = (2, 10),
    directed: bool = False,
    seed: int = SEED,
) -> tuple[nx.Graph, pd.Series]:
    """
    Build a background graph with smurfing patterns injected into it.

    Each pattern takes two existing accounts as source and target and routes
    money between them through fresh mule accounts, so source and target never
    transact directly -- the structure GARG-AML looks for.

    Parameters
    ----------
    n_nodes : int, default 200
        Size of the background graph, before mules are added.
    model : {"barabasi-albert", "erdos-renyi", "watts-strogatz"}
        Which background model to use.
    n_patterns : int, default 3
        How many smurfing patterns to inject.
    mules : tuple of int, default (2, 10)
        Inclusive range for the number of mules per pattern, drawn uniformly.
    directed : bool, default False
        Return a ``DiGraph``, with the smurfing edges oriented source to mule
        to target. Background edges keep the generator's own orientation.
    seed : int, default 1997
        Seeds the background graph and the injection.

    Returns
    -------
    graph : networkx.Graph or networkx.DiGraph
        Background plus injected patterns. Mules are named ``"mule_<i>"``.
    labels : pandas.Series
        Boolean, indexed by node, True for every account in a pattern --
        sources, targets and mules alike.

    Raises
    ------
    ValueError
        If ``model`` is unknown, or the graph is too small to place the
        requested patterns without reusing an account.

    Examples
    --------
    >>> graph, labels = smurfing_graph(n_nodes=100, n_patterns=2, seed=1)
    >>> int(labels.sum()) > 0
    True
    >>> bool(labels.loc["mule_0"])
    True
    """
    background = _background(model, n_nodes, seed)

    graph: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_nodes_from(background.nodes)
    graph.add_edges_from(background.edges)

    rng = random.Random(seed)

    # Each pattern needs its own source and target: reusing an account across
    # patterns would blur the ground truth this generator exists to provide.
    needed = 2 * n_patterns
    if needed > graph.number_of_nodes():
        raise ValueError(
            f"{n_patterns} patterns need {needed} distinct accounts, "
            f"but the background graph has {graph.number_of_nodes()}"
        )

    endpoints = rng.sample(sorted(graph.nodes, key=str), needed)
    laundering: set[Hashable] = set()
    mule_index = 0

    for pattern in range(n_patterns):
        source = endpoints[2 * pattern]
        target = endpoints[2 * pattern + 1]

        for _ in range(rng.randint(*mules)):
            mule = f"mule_{mule_index}"
            mule_index += 1
            graph.add_edge(source, mule)
            graph.add_edge(mule, target)
            laundering.add(mule)

        laundering.update((source, target))

    labels = pd.Series(
        [node in laundering for node in graph.nodes],
        index=pd.Index(list(graph.nodes), name="node"),
        name="laundering",
    )
    return graph, labels
