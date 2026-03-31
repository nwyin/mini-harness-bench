"""Data processing pipeline module.

This module started as a simple data transformer and grew over multiple
iterations. Some functions are no longer used but were never cleaned up.
"""

from __future__ import annotations

import html
import json
import math
import time
from typing import Any


class DataProcessor:
    """Main data processing class."""

    HANDLERS: dict[str, Any] = {}

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._metrics: list[dict[str, Any]] = []

    @classmethod
    def _init_handlers(cls) -> None:
        """Initialize the handler dispatch table."""
        cls.HANDLERS = {
            "decompress": cls._decompress_data,
            "identity": lambda self, data: data,
        }

    def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Main entry point: transform, validate, and format data.

        Supports an optional 'action' key in data to dispatch to a handler.
        """
        if not self.HANDLERS:
            self._init_handlers()

        action = data.get("action")
        if action and action in self.HANDLERS:
            handler = self.HANDLERS[action]
            data = handler(self, data)

        transformed = self.transform(data)
        validated = self.validate(transformed)
        return self._format_output(validated)

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply transformations to the data.

        If data contains a 'format' key, dispatches to the appropriate
        sanitizer via getattr.
        """
        result = dict(data)

        # Normalize numeric values if present
        if "values" in result:
            result["values"] = self._normalize(result["values"])

        # Apply format-specific sanitization
        fmt = result.get("format")
        if fmt:
            sanitizer_name = f"_sanitize_{fmt}"
            sanitizer = getattr(self, sanitizer_name, None)
            if sanitizer is not None:
                for key in list(result.keys()):
                    if isinstance(result[key], str) and key not in ("format", "action"):
                        result[key] = sanitizer(result[key])

        # Apply additional field transformations
        if "tags" in result:
            result["tags"] = [t.strip().lower() for t in result["tags"]]

        if "priority" in result:
            result["priority"] = max(0, min(10, result["priority"]))

        return result

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate the transformed data."""
        result = dict(data)
        errors: list[str] = []

        if "values" in result:
            for i, v in enumerate(result["values"]):
                if not self._check_bounds(v, -1e6, 1e6):
                    errors.append(f"Value at index {i} out of bounds: {v}")

        if "name" in result and not isinstance(result["name"], str):
            errors.append("name must be a string")

        if "priority" in result:
            if not isinstance(result["priority"], (int, float)):
                errors.append("priority must be numeric")

        if errors:
            result["_errors"] = errors

        return result

    def _normalize(self, values: list[float]) -> list[float]:
        """Normalize a list of values to zero mean and unit variance."""
        if not values:
            return values
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        if variance == 0:
            return [0.0] * n
        std = math.sqrt(variance)
        return [(x - mean) / std for x in values]

    def _check_bounds(self, val: float, low: float, high: float) -> bool:
        """Check if a value is within the given bounds."""
        return low <= val <= high

    def _format_output(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format the final output dictionary."""
        output: dict[str, Any] = {}
        for key, value in sorted(data.items()):
            if key.startswith("_"):
                output.setdefault("metadata", {})[key.lstrip("_")] = value
            else:
                output[key] = value
        output["processed"] = True
        return output

    def _log_metrics(self, data: dict[str, Any]) -> None:
        """Log processing metrics for monitoring.

        This was used in v1 of the pipeline but monitoring was moved to
        an external service. Kept around 'just in case'.
        """
        metric = {
            "timestamp": time.time(),
            "data_size": len(str(data)),
            "field_count": len(data),
            "has_errors": "_errors" in data,
        }
        self._metrics.append(metric)

    def _retry_with_backoff(self, fn: Any, retries: int = 3, base_delay: float = 1.0) -> Any:
        """Retry a function with exponential backoff.

        This was used when the pipeline made network calls to an external
        validation service. That service was decommissioned and validation
        is now done locally.
        """
        last_error = None
        for attempt in range(retries):
            try:
                return fn()
            except Exception as e:
                last_error = e
                delay = base_delay * (2**attempt)
                time.sleep(delay)
        raise last_error  # type: ignore[misc]

    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML content by escaping special characters."""
        return html.escape(text, quote=True)

    def _sanitize_json(self, text: str) -> str:
        """Sanitize text for safe JSON embedding."""
        # Escape characters that could break JSON strings
        return json.dumps(text)[1:-1]  # strip outer quotes

    def _compress_data(self, data: dict[str, Any]) -> bytes:
        """Compress data for storage.

        This was used when the pipeline stored results in a space-constrained
        database. The database was migrated and compression is no longer needed.
        """
        import zlib

        serialized = json.dumps(data, sort_keys=True).encode("utf-8")
        return zlib.compress(serialized)

    def _decompress_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Decompress data from the 'compressed' field.

        Used by the HANDLERS dispatch to decompress inline data before
        further processing.
        """
        import base64
        import zlib

        if "compressed" in data:
            raw = base64.b64decode(data["compressed"])
            decompressed = zlib.decompress(raw)
            payload = json.loads(decompressed.decode("utf-8"))
            result = dict(data)
            result.update(payload)
            del result["compressed"]
            return result
        return data
