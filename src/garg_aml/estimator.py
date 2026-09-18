"""
A scikit-learn compatible wrapper, for callers who work in pipelines.

Needs the ``sklearn`` extra. Import it as ``garg_aml.GargAmlScorer``; the
top-level package loads this module only when you ask for it, so scikit-learn
stays optional.
"""

import networkx as nx
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .api import score
from .features import build_features
from .preprocess import SEED, reduce_graph
from .scores import DEFAULT_SCORE_TYPE

__all__ = ["GargAmlScorer"]


class GargAmlScorer(BaseEstimator, TransformerMixin):
    """
    Turn a transaction graph into a GARG-AML feature table.

    Parameters
    ----------
    directed : bool, optional
        Which analysis to run. Taken from the graph's own type when omitted.
    score_type : {"weighted_average", "basic"}, default "weighted_average"
        Weight each block by its free entries, or take an unweighted mean.
    reduce : bool, default False
        Apply :func:`garg_aml.preprocess.reduce_graph` first.
    resolution : float, default 10
        Louvain resolution, used only when ``reduce`` is True.
    seed : int, default 1997
        Louvain seed, used only when ``reduce`` is True.
    n_jobs : int, default 1
        Processes to use; needs the ``parallel`` extra when not 1.

    Attributes
    ----------
    scores_ : pandas.DataFrame
        The scores from the last call to :meth:`fit`.
    features_ : pandas.DataFrame
        The feature table from the last call to :meth:`fit`.

    Notes
    -----
    **Nothing is learned.** GARG-AML is a closed-form structural score, so
    ``fit`` has no parameters to estimate -- it scores the graph you hand it and
    keeps the result for convenience. ``transform`` scores whatever graph it is
    given, fitted or not. The method is transductive: a node can only be scored
    as part of a graph, so there is no meaningful "apply the fitted model to
    unseen accounts" step.

    Examples
    --------
    >>> from garg_aml.synthetic import smurfing_graph
    >>> graph, labels = smurfing_graph(n_nodes=60, n_patterns=1, seed=3)
    >>> features = GargAmlScorer().fit_transform(graph)
    >>> "GARGAML" in features.columns
    True
    """

    def __init__(
        self,
        directed: bool | None = None,
        score_type: str = DEFAULT_SCORE_TYPE,
        reduce: bool = False,
        resolution: float = 10,
        seed: int = SEED,
        n_jobs: int = 1,
    ) -> None:
        self.directed = directed
        self.score_type = score_type
        self.reduce = reduce
        self.resolution = resolution
        self.seed = seed
        self.n_jobs = n_jobs

    def _features(self, graph: nx.Graph) -> tuple[pd.DataFrame, pd.DataFrame]:
        if self.reduce:
            graph = reduce_graph(graph, resolution=self.resolution, seed=self.seed)

        scores = score(
            graph,
            self.directed,
            score_type=self.score_type,
            n_jobs=self.n_jobs,
        )
        return scores, build_features(graph, scores)

    def fit(self, X: nx.Graph, y: None = None) -> "GargAmlScorer":
        """Score ``X`` and keep the result. Estimates nothing."""
        self.scores_, self.features_ = self._features(X)
        return self

    def transform(self, X: nx.Graph) -> pd.DataFrame:
        """Return the feature table for ``X``."""
        _scores, features = self._features(X)
        return features
