"""
The functions most callers need: score a graph, or score an edge list.

Everything here is a thin composition of the two stages -- block measures, then
aggregation -- so that scoring a whole graph and scoring one node give the same
numbers by construction. See ``docs/decisions/0004``.
"""

from collections.abc import Hashable, Iterable
from typing import Any

import networkx as nx
import pandas as pd

from .measures import DIRECTED_COLUMNS, UNDIRECTED_COLUMNS, block_measures
from .preprocess import SEED, reduce_graph
from .scores import DEFAULT_SCORE_TYPE, scores_from_measures

__all__ = ["block_measures_frame", "score", "score_edges"]


def _progress(nodes: list, show: bool) -> Iterable:
    if not show:
        return nodes
    try:
        from tqdm import tqdm
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "progress=True needs tqdm: pip install 'garg-aml[progress]'"
        ) from exc
    return tqdm(nodes)


def _rows(
    graph: nx.Graph, nodes: list, directed: bool, n_jobs: int, progress: bool
) -> list[tuple[float, ...]]:
    """Block measures for every node, serially or across processes."""
    views: dict[str, Any] = {}
    if directed:
        # Built once here rather than per node: deriving them inside
        # block_measures would dominate the run on any real graph.
        views = {
            "undirected": graph.to_undirected(),
            "reverse": graph.reverse(copy=True),
        }

    def measure(node: Hashable) -> tuple[float, ...]:
        return block_measures(
            graph, node, directed=directed, include_sizes=True, **views
        )

    if n_jobs == 1:
        return [measure(node) for node in _progress(nodes, progress)]

    try:
        from joblib import Parallel, delayed
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "n_jobs other than 1 needs joblib: pip install 'garg-aml[parallel]'"
        ) from exc

    # Each worker receives its own copy of the graph, so the memory cost scales
    # with n_jobs. On a large graph that is the binding constraint, not the CPU.
    return list(Parallel(n_jobs=n_jobs)(delayed(measure)(node) for node in nodes))


def block_measures_frame(
    graph: nx.Graph,
    directed: bool | None = None,
    *,
    n_jobs: int = 1,
    progress: bool = False,
) -> pd.DataFrame:
    """
    Block measures for every node of a graph.

    The expensive stage. Persist this and you can re-derive any score variant
    from it with :func:`garg_aml.scores.scores_from_measures` without touching
    the graph again.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        The graph to measure.
    directed : bool, optional
        Which analysis to run. Taken from the graph's own type when omitted.
    n_jobs : int, default 1
        Processes to use. ``-1`` means all cores, and anything other than 1
        needs the ``parallel`` extra.
    progress : bool, default False
        Show a progress bar; needs the ``progress`` extra.

    Returns
    -------
    pandas.DataFrame
        One row per node, with a ``node`` column, the block densities and the
        matching free-entry counts.

    Examples
    --------
    >>> import networkx as nx
    >>> graph = nx.Graph([("a", "m1"), ("a", "m2"), ("m1", "b"), ("m2", "b")])
    >>> frame = block_measures_frame(graph)
    >>> list(frame.columns)
    ['node', 'measure_1', 'measure_2', 'measure_3', 'size_1', 'size_2', 'size_3']
    """
    if directed is None:
        directed = nx.is_directed(graph)

    nodes = list(graph.nodes)
    columns = DIRECTED_COLUMNS if directed else UNDIRECTED_COLUMNS

    frame = pd.DataFrame(
        _rows(graph, nodes, directed, n_jobs, progress), columns=columns
    )
    frame.insert(0, "node", nodes)
    return frame


def score(
    graph: nx.Graph,
    directed: bool | None = None,
    *,
    score_type: str = DEFAULT_SCORE_TYPE,
    reduce: bool = False,
    resolution: float = 10,
    seed: int = SEED,
    n_jobs: int = 1,
    progress: bool = False,
    return_measures: bool = False,
) -> pd.DataFrame:
    """
    Score every account in a transaction graph.

    Parameters
    ----------
    graph : networkx.Graph or networkx.DiGraph
        Accounts as nodes, transactions as edges. Node identity is preserved:
        whatever your ids are, they come back as the index.
    directed : bool, optional
        Which analysis to run. Taken from the graph's own type when omitted.
    score_type : {"weighted_average", "basic"}, default "weighted_average"
        Weight each block by its free entries, or take an unweighted mean.
    reduce : bool, default False
        Apply :func:`garg_aml.preprocess.reduce_graph` first. Off by default
        because it is lossy and the choice is yours to make -- read
        ``docs/decisions/0002`` before turning it on.
    resolution, seed : float, int
        Passed to ``reduce_graph`` when ``reduce`` is True.
    n_jobs : int, default 1
        Processes to use; needs the ``parallel`` extra when not 1.
    progress : bool, default False
        Show a progress bar; needs the ``progress`` extra.
    return_measures : bool, default False
        Also return the block densities and sizes the score was built from.

    Returns
    -------
    pandas.DataFrame
        Indexed by node, with a ``GARGAML`` column in [-1, 1]. Directed graphs
        also get ``GARGAML_transposed`` and ``GARGAML_max``, which are reported
        for reference and are **not** the score (``docs/decisions/0007``).

    See Also
    --------
    score_edges : the same thing, starting from a pandas edge list.
    garg_aml.features.build_features : neighbourhood statistics on top of these.

    Notes
    -----
    Every account *in* a pattern scores high, not just the one sending the
    money: a mule's own neighbourhood has the same block structure as the
    source's. Treat a high score as "this account sits in a smurfing-shaped
    subgraph", not as "this account is the originator".

    Scores are comparable within one run. A node with no neighbours scores -1,
    and after ``reduce=True`` there are usually many of those.

    References
    ----------
    Deprez et al. (2025), Eq. (8) and Eq. (14).

    Examples
    --------
    A smurfing pattern beside a group of accounts that all trade with each
    other. The pattern scores at the top of the range; the tight group, whose
    on-diagonal blocks are full rather than empty, scores 0.

    >>> import networkx as nx
    >>> graph = nx.Graph([("a", "m1"), ("a", "m2"), ("a", "m3"),
    ...                   ("m1", "b"), ("m2", "b"), ("m3", "b"),
    ...                   ("x", "y"), ("y", "z"), ("z", "x"),
    ...                   ("x", "w"), ("y", "w"), ("z", "w")])
    >>> scores = score(graph)
    >>> float(scores.loc["a", "GARGAML"])
    1.0
    >>> float(scores.loc["x", "GARGAML"])
    0.0
    """
    if directed is None:
        directed = nx.is_directed(graph)

    if reduce:
        graph = reduce_graph(graph, resolution=resolution, seed=seed)

    measures = block_measures_frame(graph, directed, n_jobs=n_jobs, progress=progress)
    scores = scores_from_measures(measures, directed, score_type=score_type)

    if return_measures:
        return scores.join(measures.set_index("node"))
    return scores


def score_edges(
    edges: pd.DataFrame,
    source: str = "source",
    target: str = "target",
    *,
    directed: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Score accounts from a table of transactions.

    A convenience wrapper for the common case where the data is a DataFrame and
    not a graph. Parallel edges collapse -- GARG-AML reads structure, not
    volume -- and self-loops are dropped.

    Parameters
    ----------
    edges : pandas.DataFrame
        One row per transaction.
    source, target : str
        Column names holding the paying and receiving account.
    directed : bool, default False
        Build a directed graph and run the directed analysis.
    **kwargs
        Passed to :func:`score`.

    Returns
    -------
    pandas.DataFrame
        As :func:`score`.

    Examples
    --------
    >>> import pandas as pd
    >>> edges = pd.DataFrame({"source": ["a", "a", "m1", "m2"],
    ...                       "target": ["m1", "m2", "b", "b"]})
    >>> float(score_edges(edges).loc["a", "GARGAML"])
    1.0
    """
    graph: nx.Graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_edges_from(zip(edges[source], edges[target], strict=True))
    graph.remove_edges_from(nx.selfloop_edges(graph))

    return score(graph, directed, **kwargs)
