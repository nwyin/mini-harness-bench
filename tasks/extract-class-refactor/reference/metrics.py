"""MetricsCollector: extracted from AppManager to handle metrics independently."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


class MetricsCollector:
    """Collects, aggregates, and reports on numeric metrics."""

    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._metrics: dict[str, list[float]] = defaultdict(list)
        self._metrics_metadata: dict[str, dict[str, Any]] = {}
        self._metrics_start_time = time.monotonic()
        self._metrics_tags: dict[str, dict[str, str]] = {}

    def record_metric(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a single metric value."""
        full_name = f"{self.namespace}.{name}"
        self._metrics[full_name].append(value)
        if tags:
            self._metrics_tags[full_name] = {**self._metrics_tags.get(full_name, {}), **tags}
        if full_name not in self._metrics_metadata:
            self._metrics_metadata[full_name] = {
                "first_recorded": time.monotonic() - self._metrics_start_time,
                "count": 0,
            }
        self._metrics_metadata[full_name]["count"] += 1
        self._metrics_metadata[full_name]["last_recorded"] = time.monotonic() - self._metrics_start_time

    def get_metric(self, name: str) -> list[float]:
        """Get all recorded values for a metric."""
        full_name = f"{self.namespace}.{name}"
        return list(self._metrics.get(full_name, []))

    def get_all_metrics(self) -> dict[str, list[float]]:
        """Return a copy of all metrics."""
        return {k: list(v) for k, v in self._metrics.items()}

    def aggregate_metrics(self, name: str) -> dict[str, float]:
        """Return min, max, mean, count, sum for a metric."""
        values = self.get_metric(name)
        if not values:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "count": 0, "sum": 0.0}
        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "count": len(values),
            "sum": sum(values),
        }

    def reset_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()
        self._metrics_metadata.clear()
        self._metrics_tags.clear()
        self._metrics_start_time = time.monotonic()

    def export_metrics_report(self) -> dict[str, Any]:
        """Export a full metrics report with aggregates and metadata."""
        report: dict[str, Any] = {
            "namespace": self.namespace,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {},
        }
        for full_name, values in self._metrics.items():
            short_name = full_name.removeprefix(f"{self.namespace}.")
            n = len(values)
            report["metrics"][short_name] = {
                "values": values,
                "count": n,
                "sum": sum(values),
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0,
                "mean": sum(values) / n if n else 0.0,
                "tags": self._metrics_tags.get(full_name, {}),
                "metadata": self._metrics_metadata.get(full_name, {}),
            }
        return report
