import json
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "golden"

CASES = sorted(p.parent.name for p in GOLDEN.glob("*/edges.csv"))
DIRECTIONS = ["undirected", "directed"]
VARIANTS = ["raw", "reduced"]


@pytest.fixture(scope="session")
def golden() -> Path:
    return GOLDEN


@pytest.fixture(scope="session")
def manifest() -> dict:
    return json.loads((GOLDEN / "MANIFEST.json").read_text())
