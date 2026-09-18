"""
GARG-AML: graph-based detection of smurfing patterns in transaction networks.

Smurfing moves money from one account to another through intermediate mules, so
that source and target never transact directly. In the second-order
neighbourhood of such an account the adjacency matrix splits into blocks whose
on-diagonal parts are empty and whose off-diagonal parts are dense. GARG-AML
scores every account by exactly that contrast, in [-1, 1], with higher meaning
more smurfing-like. Nothing is trained and no labels are needed.

A synthetic graph of 109 accounts, 13 of them in an injected smurfing pattern.
Eight of the ten highest-scoring accounts are among those 13 -- with no
training, no labels and no tuning:

>>> import garg_aml as ga
>>> graph, labels = ga.smurfing_graph(n_nodes=100, n_patterns=2, seed=1)
>>> scores = ga.score(graph)["GARGAML"]
>>> top10 = scores.sort_values(ascending=False, kind="stable").head(10).index
>>> int(labels.reindex(top10).sum())
8

``GargAmlScorer`` is a scikit-learn compatible wrapper and needs the ``sklearn``
extra; it is imported only when you reach for it.

References
----------
Deprez, B., Baesens, B., Verdonck, T., & Verbeke, W. (2025). GARG-AML against
Smurfing: A Scalable and Interpretable Graph-Based Framework for Anti-Money
Laundering. arXiv:2506.04292.
"""

import logging
from typing import Any

from .api import block_measures_frame, score, score_edges
from .features import (
    FEATURE_COLUMNS,
    build_features,
    neighbour_degree_stats,
    neighbour_score_stats,
)
from .measures import block_measures
from .preprocess import drop_hubs, reduce_graph
from .scores import score_from_measures, scores_from_measures
from .synthetic import smurfing_graph

__version__ = "0.1.0"

# A library attaches no handlers of its own; the application decides.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "FEATURE_COLUMNS",
    "GargAmlScorer",
    "block_measures",
    "block_measures_frame",
    "build_features",
    "drop_hubs",
    "neighbour_degree_stats",
    "neighbour_score_stats",
    "reduce_graph",
    "score",
    "score_edges",
    "score_from_measures",
    "scores_from_measures",
    "smurfing_graph",
]


def __getattr__(name: str) -> Any:
    """Load the optional scikit-learn wrapper on first use."""
    if name == "GargAmlScorer":
        try:
            from .estimator import GargAmlScorer
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise ImportError(
                "GargAmlScorer needs scikit-learn: "
                "pip install 'garg-aml-smurfing[sklearn]'"
            ) from exc
        return GargAmlScorer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
