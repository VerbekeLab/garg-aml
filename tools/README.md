# Fixture tooling

`make_golden.py` and `check_golden.py` generate and verify `tests/golden/`.

**They run inside the research repository, not here.** Both import the
pre-extraction implementation from `src/methods/`, which is what the fixtures
freeze. Copy them into a checkout of
[B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML) under `scripts/` and
run from its root:

```bash
python scripts/make_golden.py     # rewrite the fixtures (a deliberate act)
python scripts/check_golden.py    # verify that implementation still reproduces them
```

They live here as the fixtures' provenance: without them there is no record of
how those numbers were produced, or how to regenerate them if the frozen
behaviour is ever deliberately changed.

From Phase 2 onward the package tests the fixtures directly against
`garg_aml` in `tests/test_golden.py`; `check_golden.py` is that test's ancestor
and is kept for comparison until the extraction is complete.
