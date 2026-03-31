"""Data transformation functions.

Applies transformations to CSV rows based on configuration.
"""

from __future__ import annotations

from datetime import datetime


def apply_transforms(rows: list[dict[str, str]], config: dict) -> list[dict[str, str]]:
    """Apply all configured transforms to the rows."""
    date_format = config.get("date_format", "%Y-%m-%d")
    date_columns = config.get("date_columns", [])
    decimal_places = config.get("decimal_places", 2)

    result = []
    for row in rows:
        transformed = dict(row)
        for col in date_columns:
            if col in transformed and transformed[col]:
                transformed[col] = normalize_date(transformed[col], date_format)
        for key, value in transformed.items():
            if key not in date_columns:
                try:
                    num = float(value)
                    transformed[key] = str(round(num, decimal_places))
                except (ValueError, TypeError):
                    pass
        result.append(transformed)
    return result


def normalize_date(value: str, fmt: str) -> str:
    """Parse a date string with the given format and return ISO format (YYYY-MM-DD)."""
    dt = datetime.strptime(value, fmt)
    return dt.strftime("%Y-%m-%d")
