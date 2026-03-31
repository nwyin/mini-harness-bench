"""CSV processing application.

Reads input CSV, applies transforms based on config, validates output,
and writes the result.
"""

from __future__ import annotations

import csv
import sys

import yaml
from transforms import apply_transforms
from validators import validate_output


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def read_csv(path: str, config: dict) -> list[dict[str, str]]:
    """Read CSV file into a list of row dicts."""
    input_cfg = config.get("input", {})
    delimiter = input_cfg.get("delimiter", ",")
    encoding = input_cfg.get("encoding", "utf-8")

    rows = []
    with open(path, encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(dict(row))
    return rows


def write_csv(rows: list[dict[str, str]], path: str, config: dict) -> None:
    """Write rows to a CSV file."""
    if not rows:
        return
    output_cfg = config.get("output", {})
    delimiter = output_cfg.get("delimiter", ",")
    encoding = output_cfg.get("encoding", "utf-8")

    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def process(input_path: str, output_path: str, config_path: str = "config.yaml") -> None:
    """Main processing pipeline."""
    config = load_config(config_path)
    rows = read_csv(input_path, config)
    transformed = apply_transforms(rows, config.get("transforms", {}))
    errors = validate_output(transformed, config.get("validation", {}))
    if errors:
        print(f"Validation errors: {errors}", file=sys.stderr)
        sys.exit(1)
    write_csv(transformed, output_path, config)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.csv> [config.yaml]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else "config.yaml"
    process(input_file, output_file, config_file)
