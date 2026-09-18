"""
Verify the golden fixtures against the current code.

This is the harness that Phase 2 ports into the package as the L1 test, so it
deliberately depends on nothing but numpy/pandas/networkx and the frozen CSVs
in ``golden/`` -- no igraph, no seeds, no generator. Run it after any change to
``src/methods/`` or ``src/utils/graph_processing.py``, and on a different
networkx to check the fixtures are portable:

    python scripts/check_golden.py

Exit code is non-zero if anything drifted.
"""

import glob
import os
import sys

DIR = "./"
os.chdir(DIR)
sys.path.append(DIR)

import networkx as nx
import pandas as pd

from src.utils.graph_processing import graph_community

sys.path.insert(0, "scripts")
from make_golden import (  # noqa: E402  -- reuses the generator's own stages
    GOLDEN_DIR,
    RESOLUTION,
    edge_frame,
    features_frame,
    load_graph,
    measures_frame,
    node_frame,
    scores_frame,
)

RTOL = 1e-12


def compare(name, produced, expected, results):
    """Assert two frames match, and record the outcome rather than raising."""
    try:
        pd.testing.assert_frame_equal(
            produced.reset_index(drop=True),
            expected.reset_index(drop=True),
            rtol=RTOL,
            check_dtype=False,
        )
    except AssertionError as exc:
        results.append((name, str(exc).strip().split("\n")[0]))
        return False
    return True


def check_case(case, results):
    case_dir = os.path.join(GOLDEN_DIR, case)
    checked = 0

    for directed in [False, True]:
        label = "directed" if directed else "undirected"
        G = load_graph(os.path.join(case_dir, "edges.csv"), directed)

        # reduce_graph: the version-sensitive one. Louvain's partition is an
        # implementation detail of networkx, so this is the fixture expected to
        # break first on an upgrade -- deliberately isolated from the rest.
        reduced = graph_community(G, resolution=RESOLUTION)
        expected_reduced = pd.read_csv(
            os.path.join(case_dir, f"reduced_edges_{label}.csv")
        )
        compare(f"{case}/reduce_graph.edges[{label}]", edge_frame(reduced),
                expected_reduced, results)
        compare(f"{case}/reduce_graph.nodes[{label}]", node_frame(reduced),
                pd.read_csv(os.path.join(case_dir, f"reduced_nodes_{label}.csv")),
                results)
        checked += 2

        # Everything downstream is computed from the *frozen* reduced edge
        # list, not from what Louvain just produced, so a partition change
        # cannot cascade.
        variants = {
            "raw": G,
            "reduced": load_graph(
                os.path.join(case_dir, f"reduced_edges_{label}.csv"), directed,
                nodes_path=os.path.join(case_dir, f"reduced_nodes_{label}.csv"),
            ),
        }
        for variant, graph in variants.items():
            measures = measures_frame(graph, directed)
            stem = f"{label}_{variant}"

            compare(f"{case}/measures[{stem}]", measures,
                    pd.read_csv(os.path.join(case_dir, f"measures_{stem}.csv")),
                    results)
            compare(f"{case}/scores[{stem}]", scores_frame(measures, directed),
                    pd.read_csv(os.path.join(case_dir, f"scores_{stem}.csv"),
                                index_col="node"),
                    results)
            compare(f"{case}/features[{stem}]",
                    features_frame(graph, measures, directed),
                    pd.read_csv(os.path.join(case_dir, f"features_{stem}.csv"),
                                index_col="node"),
                    results)
            checked += 3

    return checked


if __name__ == "__main__":
    cases = sorted(
        os.path.basename(os.path.dirname(p))
        for p in glob.glob(os.path.join(GOLDEN_DIR, "*", "edges.csv"))
    )
    if not cases:
        sys.exit(f"No fixtures in {GOLDEN_DIR}/ -- run scripts/make_golden.py first")

    print(f"networkx {nx.__version__} | pandas {pd.__version__}")

    results, checked = [], 0
    for case in cases:
        checked += check_case(case, results)

    print(f"\n{checked} comparisons across {len(cases)} cases")
    if results:
        print(f"{len(results)} MISMATCH(ES):")
        for name, detail in results:
            print(f"  {name}: {detail}")
        sys.exit(1)
    print("all fixtures reproduce")
