# Changelog

All notable changes to this project are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html); while the version
is `0.x` the public API may change with a minor bump, always with an entry here.

## [Unreleased]

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

### Notes

- Public names are still the research repository's (`GARG_AML_node_*_measures`,
  `define_gargaml_scores`, ...). Renaming to PEP 8, type hints and NumPy-style
  docstrings follow in the next release step, with the fixtures green throughout.
- The original's bare `except:` around the neighbour statistics is written as the
  explicit empty check it always was. Same result, verified by both test layers.
