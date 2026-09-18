# Contributing and maintaining

This file is the maintainer's manual. If you have inherited this package and
read nothing else, read this and `docs/decisions/`.

## Setup

Keep the virtual environment **outside** the repository — the working clone sits
in a OneDrive folder, which would otherwise sync all of `site-packages`.

```bash
python -m venv ~/.venvs/garg-aml
source ~/.venvs/garg-aml/bin/activate
pip install -e ".[dev,docs,progress,parallel,sklearn]"
pre-commit install
```

## The rules that matter

**1. `tests/golden/` is frozen behaviour, not test scaffolding.** Those files
were generated from the implementation that produced the published paper
results. Never edit one to make a test pass — a diff means the code changed.
Regenerating them is a separate commit with its own justification, and it
invalidates comparability with everything published before it.

**2. Some edge cases look like bugs and are not.** An off-diagonal block with no
free entries has density 1; a node whose block sizes are all zero scores -1;
isolated nodes get zero for every neighbour statistic. Each has an ADR in
`docs/decisions/`. Changing any of them changes every published number.

**3. The library does no I/O and prints nothing.** Objects in, objects out. No
file paths, no `os.chdir`, no `print`. Use `logging.getLogger("garg_aml")`.

**4. Core dependencies are numpy, pandas, networkx and scipy.** Everything else
is an optional extra behind a guarded import. In particular the package must
never depend on PyTorch.

## Checks

```bash
ruff check . && ruff format --check .
mypy
pytest
```

`pre-commit run --all-files` runs the first two. CI runs all three on Python
3.10-3.13, plus a weekly scheduled run against unpinned dependencies so that
upstream drift surfaces before a user reports it.

Coverage must stay at or above 90 %, and that is a hard failure rather than a
badge.

## Definition of done

1. Golden tests pass unchanged.
2. `ruff` and `mypy` are clean.
3. Public API has a NumPy-style docstring with a paper reference and a runnable
   doctest.
4. `CHANGELOG.md` updated in the same commit as the change.
5. Any non-obvious decision recorded as an ADR in `docs/decisions/`.

## Releasing

Publishing uses **PyPI Trusted Publishing** from GitHub Actions. There is no API
token anywhere, so nothing has to be rotated or handed over.

1. Update `CHANGELOG.md`: move `[Unreleased]` entries under the new version.
2. Bump `__version__` in `src/garg_aml/__init__.py` and `version:` in
   `CITATION.cff`.
3. Commit, then tag: `git tag v0.1.0 && git push origin main --tags`.
4. The `release` workflow builds and publishes; Zenodo mints a DOI from the
   GitHub release.

### If you cannot publish to PyPI

The `garg-aml` name has a single owner. If that account is unreachable, the code
is still safe — it lives in the `VerbekeLab` organisation — but the name is not
reclaimable quickly. Publish under a new name instead: change `name` in
`pyproject.toml`, register Trusted Publishing for the new project, and release
as above. The Zenodo DOI and git tags remain the citable artefacts either way,
so nothing published in a paper depends on PyPI being writable.

## Where things live

| | |
|---|---|
| `src/garg_aml/` | the library; leading-underscore modules are private |
| `tests/golden/` | frozen fixtures — see `tests/golden/README.md` |
| `tools/` | the fixture generator; runs in the research repo, not here |
| `docs/decisions/` | architecture decision records |
| [B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML) | experiments, baselines, paper reproduction |
