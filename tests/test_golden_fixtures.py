"""
Integrity of the frozen fixtures themselves.

These check that the oracle is complete and internally consistent. They do not
touch ``garg_aml`` -- comparing the implementation against these numbers is
``test_golden.py``, which arrives with the first extracted module.
"""

import pandas as pd
import pytest

from .conftest import CASES, DIRECTIONS, VARIANTS

MEASURE_COLUMNS = {
    "undirected": 3,
    "directed": 9,
}


def test_cases_are_present():
    assert CASES == ["synth_ba", "synth_er", "synth_ws", "toy"]


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
def test_reduced_graph_is_frozen_as_nodes_and_edges(golden, case, direction):
    # An edge list alone loses the isolated nodes Louvain leaves behind, and
    # those are exactly what exercises the frozen degenerate cases.
    for part in ("nodes", "edges"):
        assert (golden / case / f"reduced_{part}_{direction}.csv").exists()


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_stages_cover_the_same_nodes(golden, case, direction, variant):
    stem = f"{direction}_{variant}"
    measures = pd.read_csv(golden / case / f"measures_{stem}.csv")
    scores = pd.read_csv(golden / case / f"scores_{stem}.csv", index_col="node")
    features = pd.read_csv(golden / case / f"features_{stem}.csv", index_col="node")

    nodes = sorted(measures["node"])
    assert sorted(scores.index) == nodes
    assert sorted(features.index) == nodes


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_measure_and_size_columns_match_the_block_grid(
    golden, case, direction, variant
):
    measures = pd.read_csv(golden / case / f"measures_{direction}_{variant}.csv")
    expected = MEASURE_COLUMNS[direction]

    assert sum(c.startswith("measure_") for c in measures.columns) == expected
    assert sum(c.startswith("size_") for c in measures.columns) == expected


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("variant", VARIANTS)
def test_every_score_is_in_range(golden, case, direction, variant):
    scores = pd.read_csv(
        golden / case / f"scores_{direction}_{variant}.csv", index_col="node"
    )
    assert scores.min().min() >= -1
    assert scores.max().max() <= 1


def test_toy_smurfing_source_scores_one(golden):
    # Node 23 pays 20/21/22, which all pay 19: the textbook pattern, and the
    # only score in the fixtures that is exactly at the top of the range.
    scores = pd.read_csv(golden / "toy" / "scores_undirected_raw.csv", index_col="node")
    assert scores.loc[23, "weighted_average__GARGAML"] == 1.0


def test_isolated_nodes_return_the_frozen_values(golden):
    # Louvain at resolution 10 strands most of the toy graph. ADR 0003.
    features = pd.read_csv(
        golden / "toy" / "features_undirected_reduced.csv", index_col="node"
    )
    isolated = features[features["degree"] == 0]
    assert len(isolated) == 18

    statistics = [c for c in features.columns if c not in ("GARGAML", "degree")]
    assert (isolated[statistics] == 0).all().all()
    assert (isolated["GARGAML"] == -1).all()


def test_manifest_records_its_provenance(manifest):
    assert manifest["source_commit"]
    assert manifest["settings"]["seed"] == 1997
    assert manifest["settings"]["louvain_resolution"] == 10
    for package in ("networkx", "numpy", "pandas"):
        assert manifest["environment"][package]
