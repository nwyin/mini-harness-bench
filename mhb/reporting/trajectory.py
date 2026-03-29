from __future__ import annotations

import json
from pathlib import Path


def write_trajectory(events: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def read_trajectory(path: Path) -> list[dict]:
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events
