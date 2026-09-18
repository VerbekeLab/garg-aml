"""
Aggregation of block measures into the GARG-AML score: the cheap second stage.

Two aggregations. ``basic`` takes an unweighted mean over the blocks;
``weighted_average`` weights each block by its number of free entries, which is
Eq. (8) undirected and the size-weighted form of Eq. (14) directed.
``weighted_average`` is the default because it is what the paper reports -- see
``docs/decisions/0001``.

For a directed graph the score is Eq. (14) on the graph's given orientation.
:func:`scores_from_measures` also reports the same quantity computed on the
transpose, and the larger of the two, for reference. Neither is the score, and
the transpose-max is **not** the paper's reverse-flow handling -- that lives in
the level assignment. See ``docs/decisions/0007``.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

__all__ = ["score_from_measures", "scores_from_measures"]

#: One node's block measures: a plain mapping, or a row of a measures frame.
MeasureRow = Mapping[str, Any] | pd.Series

#: What the published experiments use.
DEFAULT_SCORE_TYPE = "weighted_average"

SCORE_TYPES = ("basic", "weighted_average")


def _check_score_type(score_type: str) -> None:
    if score_type not in SCORE_TYPES:
        raise ValueError(
            f"unknown score_type {score_type!r}; expected one of {SCORE_TYPES}"
        )


def _directed_score(row: MeasureRow, score_type: str) -> tuple[float, float]:
    """Eq. (14) on the given orientation, and the same on the transpose."""
    _check_score_type(score_type)

    measure_00 = row["measure_00"]
    measure_01 = row["measure_01"]
    measure_02 = row["measure_02"]
    measure_10 = row["measure_10"]
    measure_11 = row["measure_11"]
    measure_12 = row["measure_12"]
    measure_20 = row["measure_20"]
    measure_21 = row["measure_21"]
    measure_22 = row["measure_22"]

    dense = [measure_01, measure_12]
    sparse = [
        measure_10,
        measure_21,
        measure_00,
        measure_02,
        measure_11,
        measure_20,
        measure_22,
    ]
    dense_t = [measure_10, measure_21]
    sparse_t = [
        measure_01,
        measure_12,
        measure_00,
        measure_20,
        measure_11,
        measure_02,
        measure_22,
    ]

    if score_type == "basic":
        return (
            float(np.mean(dense) - np.mean(sparse)),
            float(np.mean(dense_t) - np.mean(sparse_t)),
        )

    size_00 = row["size_00"]
    size_01 = row["size_01"]
    size_02 = row["size_02"]
    size_10 = row["size_10"]
    size_11 = row["size_11"]
    size_12 = row["size_12"]
    size_20 = row["size_20"]
    size_21 = row["size_21"]
    size_22 = row["size_22"]

    dense_sizes = [size_01, size_12]
    sparse_sizes = [size_10, size_21, size_00, size_02, size_11, size_20, size_22]
    dense_sizes_t = [size_10, size_21]
    sparse_sizes_t = [size_01, size_12, size_00, size_20, size_11, size_02, size_22]

    return (
        _weighted(dense, dense_sizes) - _weighted(sparse, sparse_sizes),
        _weighted(dense_t, dense_sizes_t) - _weighted(sparse_t, sparse_sizes_t),
    )


def _weighted(measures: list[float], sizes: list[int]) -> float:
    """Size-weighted mean, falling back to the plain mean when every size is 0."""
    total = sum(sizes)
    if total > 0:
        return sum(m * s for m, s in zip(measures, sizes, strict=True)) / total
    return float(np.mean(measures))


def _undirected_score(row: MeasureRow, score_type: str) -> float:
    """Eq. (8)."""
    _check_score_type(score_type)

    measure_1 = row["measure_1"]
    measure_2 = row["measure_2"]
    measure_3 = row["measure_3"]

    if score_type == "basic":
        return measure_2 - (measure_1 + measure_3) / 2

    size_1 = row["size_1"]
    size_2 = row["size_2"]
    size_3 = row["size_3"]

    total = size_1 + size_3
    if total > 0:
        return measure_2 - (size_1 * measure_1 + size_3 * measure_3) / total
    if size_2 > 0:
        return measure_2  # only the off-diagonal block carries any information
    return -1  # no neighbourhood at all: as far from smurfing as the range goes


def score_from_measures(
    row: MeasureRow, directed: bool = False, score_type: str = DEFAULT_SCORE_TYPE
) -> float:
    """
    Return the GARG-AML score for one node's block measures.

    Parameters
    ----------
    row : mapping
        Block measures for one node, keyed as :func:`block_measures` names them:
        ``measure_1`` to ``measure_3`` undirected, ``measure_00`` to
        ``measure_22`` directed, plus the matching ``size_*`` entries when
        ``score_type`` is ``"weighted_average"``. A row of the frame written by
        :func:`scores_from_measures`' input works directly.
    directed : bool, default False
        Use Eq. (14) rather than Eq. (8).
    score_type : {"weighted_average", "basic"}, default "weighted_average"
        Weight each block by its free entries, or take an unweighted mean.

    Returns
    -------
    float
        A score in [-1, 1]. Higher is more smurfing-like; 1 is a pure pattern.

    Raises
    ------
    ValueError
        If ``score_type`` is not one of the two known values.

    References
    ----------
    Deprez et al. (2025), Eq. (8) and Eq. (14).

    Examples
    --------
    >>> row = {"measure_1": 0.0, "measure_2": 1.0, "measure_3": 0.0,
    ...        "size_1": 0, "size_2": 2, "size_3": 2}
    >>> score_from_measures(row)
    1.0
    """
    if directed:
        score, _transposed = _directed_score(row, score_type)
        return score
    return _undirected_score(row, score_type)


def scores_from_measures(
    measures: pd.DataFrame, directed: bool = False, score_type: str = DEFAULT_SCORE_TYPE
) -> pd.DataFrame:
    """
    Scores for a frame of block measures.

    Parameters
    ----------
    measures : pandas.DataFrame
        One row per node, with a ``node`` column and the measure and size
        columns :func:`block_measures` produces.
    directed : bool, default False
        Use Eq. (14) rather than Eq. (8).
    score_type : {"weighted_average", "basic"}, default "weighted_average"
        Weight each block by its free entries, or take an unweighted mean.

    Returns
    -------
    pandas.DataFrame
        Indexed by node. Undirected: a ``GARGAML`` column. Directed: also
        ``GARGAML_transposed`` and ``GARGAML_max``, which are reported for
        reference and are not the score -- see ``docs/decisions/0007``.

    Examples
    --------
    >>> import pandas as pd
    >>> measures = pd.DataFrame({"node": ["a"], "measure_1": [0.0],
    ...                          "measure_2": [1.0], "measure_3": [0.0],
    ...                          "size_1": [0], "size_2": [2], "size_3": [2]})
    >>> float(scores_from_measures(measures).loc["a", "GARGAML"])
    1.0
    """
    if directed:
        pairs = [_directed_score(row, score_type) for _, row in measures.iterrows()]
        frame = pd.DataFrame(
            {
                "node": measures["node"].tolist(),
                "GARGAML": [score for score, _ in pairs],
                "GARGAML_transposed": [transposed for _, transposed in pairs],
                "GARGAML_max": [max(pair) for pair in pairs],
            }
        )
    else:
        frame = pd.DataFrame(
            {
                "node": measures["node"].tolist(),
                "GARGAML": [
                    _undirected_score(row, score_type) for _, row in measures.iterrows()
                ],
            }
        )

    return frame.set_index("node")
