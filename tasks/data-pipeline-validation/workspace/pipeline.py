"""Data pipeline with schema validation and transformations.

Implement the functions below. See task.yaml for detailed requirements.
"""

from __future__ import annotations

from typing import Any


def read_csv(path: str) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts.

    All values are returned as strings (raw from CSV).
    The first row is treated as the header.
    Returns an empty list for empty files or files with only a header.
    """
    raise NotImplementedError


def validate_schema(
    rows: list[dict[str, str]],
    schema: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate rows against a schema and coerce types.

    Schema maps column names to types: "str", "int", "float", "bool".
    - Missing columns in a row produce an error for that row.
    - Type conversion failures produce an error for that row.
    - Extra columns not in the schema are kept as-is (strings).
    - Bool conversion: "true"/"1"/"yes" -> True, "false"/"0"/"no" -> False (case-insensitive)

    Returns (valid_rows_with_coerced_types, list_of_error_messages).
    Each error message should include the row index and column name.
    """
    raise NotImplementedError


def transform(
    rows: list[dict[str, Any]],
    transforms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply a list of transformations to each row.

    Each transform dict has:
    - "column": the column to transform
    - "operation": one of "upper", "lower", "round", "strip", "abs"
    - Additional params depending on operation (e.g., "decimals" for round)

    If a column doesn't exist in a row, skip that transform for that row.
    If the value type doesn't match the operation, skip it.
    """
    raise NotImplementedError


def validate_output(
    rows: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """Validate output rows against a list of constraints.

    Each constraint dict has:
    - "column": the column to check
    - "rule": one of "not_null", "unique", "min", "max", "in"
    - "value": the constraint value (depends on rule)

    Rules:
    - not_null: value in column must not be None or empty string
    - unique: all values in the column must be unique
    - min: numeric value must be >= constraint value
    - max: numeric value must be <= constraint value
    - in: value must be in the constraint value list

    Returns (all_passed, list_of_error_messages).
    """
    raise NotImplementedError


def write_csv(rows: list[dict[str, Any]], path: str) -> None:
    """Write a list of row dicts to a CSV file.

    Columns are determined from the keys of the first row.
    All values are converted to strings.
    """
    raise NotImplementedError
