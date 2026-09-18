# Changelog

All notable changes to this project are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html); while the version
is `0.x` the public API may change with a minor bump, always with an entry here.

## [Unreleased]

## [0.1.0] - 2026-09-18

First public release. The GARG-AML scoring core, extracted from the research
repository that accompanies the paper, with its behaviour pinned to the
implementation that produced the published results.

### Added

- Project skeleton: packaging, lint/type/test configuration, CI and docs scaffold.
- Frozen-behaviour fixtures under `tests/golden/`, generated from the
  pre-extraction implementation, with the tooling that built them in `tools/`.
- Initial architecture decision records under `docs/decisions/`.
- The GARG-AML scoring core, moved across from the research repository with its
  function bodies unchanged: `_blocks` (the 3 undirected and 9 directed block
  densities), `_ordering` (the level assignment), `measures` (per-node block
  measures), `scores` (aggregation into the score), `preprocess` (Louvain
  reduction, hub removal) and `features` (neighbourhood summary statistics).
- `tests/test_golden.py`, comparing every stage against the frozen fixtures, and
  `tests/test_equivalence.py`, comparing the moved code against the
  implementation it came from over 22 graph shapes in both directions. The
  latter needs the research repository present and is removed once the
  extraction is complete.

- Public API: `score`, `score_edges`, `block_measures_frame`, and the
  `GargAmlScorer` scikit-learn wrapper (optional, loaded on first use so that
  scikit-learn stays out of the import path). `__all__` now lists exactly what
  is supported.
- `smurfing_graph`, a networkx generator of graphs with known patterns, so the
  documentation and tests run with no data download.
- `n_jobs` on the scoring entry points, and `progress` for a progress bar.
- A documentation site: quickstart, how it works, five guide pages, scaling,
  limitations, API reference and the decision log. Every `>>>` example in the
  docs is executed by the test suite.

### Changed

- PEP 8 names throughout, with the two per-node measure functions merged into
  one `block_measures(graph, node, directed=False)`:

  | was | is |
  |---|---|
  | `GARG_AML_node_{un,}directed_measures` | `block_measures` |
  | `calculate_score_{un,}directed` | `score_from_measures` |
  | `define_gargaml_scores` | `scores_from_measures` |
  | `graph_community` | `reduce_graph` |
  | `graph_degree` | `drop_hubs` |
  | `summaries_neighbourhoors_node` | `neighbour_score_stats` |
  | `degree_neighbours_node` | `neighbour_degree_stats` |
  | `summarise_gargaml_scores` | `build_features` |
  | `measure_NN_function` | private `_block_NN` |

- **`score_type` now defaults to `"weighted_average"`**, the aggregation every
  published experiment uses. The previous default, `"basic"`, gives different
  numbers.
- `reduce_graph` takes `seed` (default 1997) rather than hard-coding it.
- `build_features` returns every feature column by default rather than only the
  score.
- Node identity is preserved: the old directed path cast integer node ids to
  float. Cosmetic, but the package no longer does it — see `docs/decisions/0008`.
- Type hints on every function and NumPy-style docstrings with paper references
  on every public one, each carrying a doctest that runs in CI.

### Notes

- The original's bare `except:` around the neighbour statistics is written as the
  explicit empty check it always was. Same result, verified by both test layers.

[Unreleased]: https://github.com/VerbekeLab/garg-aml/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/VerbekeLab/garg-aml/releases/tag/v0.1.0
