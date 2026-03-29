"""Data pipeline with schema validation and transformations."""

from __future__ import annotations

import csv
from typing import Any


def read_csv(path: str) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts."""
    rows: list[dict[str, str]] = []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    except FileNotFoundError:
        return []
    return rows


def _coerce_bool(value: str) -> bool:
    """Convert string to bool."""
    lower = value.strip().lower()
    if lower in ("true", "1", "yes"):
        return True
    if lower in ("false", "0", "no"):
        return False
    raise ValueError(f"Cannot convert {value!r} to bool")


def validate_schema(
    rows: list[dict[str, str]],
    schema: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate rows against a schema and coerce types."""
    valid_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    type_map = {
        "str": str,
        "int": int,
        "float": float,
        "bool": _coerce_bool,
    }

    for i, row in enumerate(rows):
        coerced: dict[str, Any] = {}
        row_valid = True

        for col, type_name in schema.items():
            if col not in row:
                errors.append(f"Row {i}: missing column '{col}'")
                row_valid = False
                continue
            converter = type_map.get(type_name, str)
            try:
                coerced[col] = converter(row[col])
            except (ValueError, TypeError) as exc:
                errors.append(f"Row {i}: column '{col}' type error: {exc}")
                row_valid = False

        if row_valid:
            # Keep extra columns as strings
            for col, val in row.items():
                if col not in schema:
                    coerced[col] = val
            valid_rows.append(coerced)

    return valid_rows, errors


def transform(
    rows: list[dict[str, Any]],
    transforms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply a list of transformations to each row."""
    result = []
    for row in rows:
        new_row = dict(row)
        for t in transforms:
            col = t["column"]
            op = t["operation"]
            if col not in new_row:
                continue
            val = new_row[col]

            if op == "upper" and isinstance(val, str):
                new_row[col] = val.upper()
            elif op == "lower" and isinstance(val, str):
                new_row[col] = val.lower()
            elif op == "strip" and isinstance(val, str):
                new_row[col] = val.strip()
            elif op == "round" and isinstance(val, (int, float)):
                decimals = t.get("decimals", 0)
                new_row[col] = round(val, decimals)
            elif op == "abs" and isinstance(val, (int, float)):
                new_row[col] = abs(val)

        result.append(new_row)
    return result


def validate_output(
    rows: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """Validate output rows against a list of constraints."""
    errors: list[str] = []

    for constraint in constraints:
        col = constraint["column"]
        rule = constraint["rule"]
        value = constraint.get("value")

        if rule == "not_null":
            for i, row in enumerate(rows):
                v = row.get(col)
                if v is None or v == "":
                    errors.append(f"Row {i}: column '{col}' is null or empty")

        elif rule == "unique":
            seen: dict[Any, int] = {}
            for i, row in enumerate(rows):
                v = row.get(col)
                if v in seen:
                    errors.append(f"Row {i}: column '{col}' value {v!r} duplicates row {seen[v]}")
                else:
                    seen[v] = i

        elif rule == "min":
            for i, row in enumerate(rows):
                v = row.get(col)
                if isinstance(v, (int, float)) and v < value:
                    errors.append(f"Row {i}: column '{col}' value {v} < min {value}")

        elif rule == "max":
            for i, row in enumerate(rows):
                v = row.get(col)
                if isinstance(v, (int, float)) and v > value:
                    errors.append(f"Row {i}: column '{col}' value {v} > max {value}")

        elif rule == "in":
            for i, row in enumerate(rows):
                v = row.get(col)
                if v not in value:
                    errors.append(f"Row {i}: column '{col}' value {v!r} not in {value}")

    return len(errors) == 0, errors


def write_csv(rows: list[dict[str, Any]], path: str) -> None:
    """Write a list of row dicts to a CSV file."""
    if not rows:
        with open(path, "w", newline="") as f:
            f.write("")
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: str(v) for k, v in row.items()})
