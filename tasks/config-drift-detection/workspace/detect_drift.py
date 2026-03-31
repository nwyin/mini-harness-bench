"""Detect configuration drift between expected/ and deployed/ directories."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into dot-notation keys."""
    items: dict[str, Any] = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, full_key))
        else:
            items[full_key] = value
    return items


def compare_configs(expected: dict[str, Any], deployed: dict[str, Any], filename: str) -> list[dict[str, Any]]:
    """Compare two config dicts and return a list of drift entries."""
    drifts: list[dict[str, Any]] = []
    exp_flat = flatten_dict(expected)
    dep_flat = flatten_dict(deployed)

    all_keys = set(exp_flat.keys()) | set(dep_flat.keys())
    for key in sorted(all_keys):
        in_exp = key in exp_flat
        in_dep = key in dep_flat

        if in_exp and in_dep:
            if exp_flat[key] != dep_flat[key]:
                drifts.append(
                    {
                        "file": filename,
                        "type": "value_changed",
                        "path": key,
                        "expected": exp_flat[key],
                        "actual": dep_flat[key],
                    }
                )
        elif in_exp and not in_dep:
            drifts.append(
                {
                    "file": filename,
                    "type": "key_missing_in_deployed",
                    "path": key,
                    "expected": exp_flat[key],
                    "actual": None,
                }
            )
        else:  # in_dep and not in_exp
            drifts.append(
                {
                    "file": filename,
                    "type": "key_added_in_deployed",
                    "path": key,
                    "expected": None,
                    "actual": dep_flat[key],
                }
            )

    return drifts


def detect_drift(expected_dir: Path, deployed_dir: Path) -> dict[str, Any]:
    """Compare all JSON files between expected and deployed directories."""
    drifts: list[dict[str, Any]] = []
    files_checked = set()
    files_with_drifts = set()

    # Check all expected files
    for exp_file in sorted(expected_dir.glob("*.json")):
        filename = exp_file.name
        files_checked.add(filename)
        dep_file = deployed_dir / filename

        if not dep_file.exists():
            drifts.append({"file": filename, "type": "file_missing_in_deployed"})
            files_with_drifts.add(filename)
            continue

        expected = json.loads(exp_file.read_text())
        deployed = json.loads(dep_file.read_text())
        file_drifts = compare_configs(expected, deployed, filename)
        if file_drifts:
            files_with_drifts.add(filename)
        drifts.extend(file_drifts)

    # Check for files only in deployed
    for dep_file in sorted(deployed_dir.glob("*.json")):
        filename = dep_file.name
        if filename not in files_checked:
            files_checked.add(filename)
            drifts.append({"file": filename, "type": "file_added_in_deployed"})
            files_with_drifts.add(filename)

    return {
        "drifts": drifts,
        "summary": {
            "total_files_checked": len(files_checked),
            "files_with_drifts": len(files_with_drifts),
            "total_drifts": len(drifts),
        },
    }


def main() -> None:
    expected_dir = Path("expected")
    deployed_dir = Path("deployed")

    if len(sys.argv) >= 3:
        expected_dir = Path(sys.argv[1])
        deployed_dir = Path(sys.argv[2])

    report = detect_drift(expected_dir, deployed_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
