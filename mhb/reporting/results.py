from __future__ import annotations

import json
from pathlib import Path


def write_results(results: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2)


def read_results(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)
