"""
The L1 test: garg_aml must reproduce the frozen fixtures exactly.

These numbers came from the implementation that produced the published paper
results. A failure here means the code changed, never that a fixture needs
updating -- see tests/golden/README.md.
"""

import pandas as pd
import pytest

from garg_aml.preprocess import reduce_graph

from ._pipeline import (
    edge_frame,
    features_frame,
    index_values,
    load_graph,
    measures_frame,
    node_frame,
    scores_frame,
)
from .conftest import CASES, DIRECTIONS, VARIANTS

RTOL = 1e-12
RESOLUTION = 10


def _graph(golden, case, direction, variant):
    case_dir = golden / case
    directed = direction == "directed"
    if variant == "raw":
        return load_graph(case_dir / "edges.csv", directed)
    return load_graph(
        case_dir / f"reduced_edges_{direction}.csv",
        directed,
        nodes_path=case_dir / f"reduced_nodes_{direction}.csv",
    )


def _same(produced, expected):
    # Indices are compared by value, not by dtype. The directed score and
    # feature fixtures carry a *float* node index because the old
    # implementation collected node ids through DataFrame.iterrows(), which
    # coerces a row to one dtype; the package preserves whatever the caller's
    # node ids are. See docs/decisions/0008.
    assert index_values(produced) == index_values(expected)

    pd.testing.assert_frame_equal(
        produced.reset_index(drop=True),
        expected.reset_index(drop=True),
        rtol=RTOL,
        check_dtype=False,
    )


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_reduce_graph_reproduces_the_frozen_partition(golden, case, direction):
    # The version-sensitive fixture: Louvain's partition is networkx's to
    # change. Kept separate so an upgrade breaks this and nothing else.
    G = load_graph(golden / case / "edges.csv", direction == "directed")
    reduced = reduce_graph(G, resolution=RESOLUTION)

    _same(
        node_frame(reduced),
        pd.read_csv(golden / case / f"reduced_nodes_{direction}.csv"),
    )
    _same(
        edge_frame(reduced),
        pd.read_csv(golden / case / f"reduced_edges_{direction}.csv"),
    )


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_measures_reproduce(golden, case, direction, variant):
    graph = _graph(golden, case, direction, variant)
    produced = measures_frame(graph, direction == "directed")
    _same(produced, pd.read_csv(golden / case / f"measures_{direction}_{variant}.csv"))


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_scores_reproduce(golden, case, direction, variant):
    directed = direction == "directed"
    graph = _graph(golden, case, direction, variant)
    produced = scores_frame(measures_frame(graph, directed), directed)
    _same(
        produced,
        pd.read_csv(
            golden / case / f"scores_{direction}_{variant}.csv", index_col="node"
        ),
    )


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_features_reproduce(golden, case, direction, variant):
    directed = direction == "directed"
    graph = _graph(golden, case, direction, variant)
    produced = features_frame(graph, measures_frame(graph, directed), directed)
    _same(
        produced,
        pd.read_csv(
            golden / case / f"features_{direction}_{variant}.csv", index_col="node"
        ),
    )
