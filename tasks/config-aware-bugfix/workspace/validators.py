"""Output validation functions.

Validates transformed data against the configured schema.
"""

from __future__ import annotations


def validate_output(rows: list[dict[str, str]], config: dict) -> list[str]:
    """Validate rows against the configured schema.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []
    required_columns = config.get("required_columns", [])
    max_rows = config.get("max_rows", 10000)

    if len(rows) > max_rows:
        errors.append(f"Too many rows: {len(rows)} > {max_rows}")

    if rows:
        columns = set(rows[0].keys())
        for col in required_columns:
            if col not in columns:
                errors.append(f"Missing required column: {col}")

    for i, row in enumerate(rows):
        for col in required_columns:
            if col in row and not row[col].strip():
                errors.append(f"Row {i + 1}: empty value in required column '{col}'")

    return errors
