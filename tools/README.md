# Fixture tooling

`make_golden.py` generated `tests/golden/` from the pre-extraction
implementation. It lives here as the fixtures' provenance: without it there is
no record of how those numbers were produced, or how to regenerate them if the
frozen behaviour is ever deliberately changed.

**It runs inside the research repository, not here.** It imports the old
implementation from `src/methods/`, which is what the fixtures freeze. Copy it
into a checkout of
[B-Deprez/GARG-AML](https://github.com/B-Deprez/GARG-AML) under `scripts/` and
run from its root:

```bash
python scripts/make_golden.py
```

Regenerating the fixtures is a deliberate act with its own justification: it
invalidates comparability with everything published before it. See
`tests/golden/README.md`.

The package itself checks the fixtures in `tests/test_golden.py`, which needs
nothing from this directory.
