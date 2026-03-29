"""Utility functions that interact with AppManager and MetricsCollector."""

from __future__ import annotations

from typing import Any

from monolith import AppManager


def timed_operation(app: AppManager, operation_name: str, duration_ms: float) -> None:
    """Record timing metrics for an operation."""
    app.record_metric(f"op.{operation_name}.duration_ms", duration_ms)
    app.debug(f"Operation {operation_name} took {duration_ms}ms")


def record_error_metrics(app: AppManager, error_type: str, count: int = 1) -> None:
    """Record error metrics for tracking failure rates."""
    for _ in range(count):
        app.record_metric(f"errors.{error_type}", 1.0)
    app.warning(f"Recorded {count} error(s) of type {error_type}")


def build_metrics_summary(app: AppManager, metric_names: list[str]) -> dict[str, Any]:
    """Build a summary dict with aggregates for each named metric."""
    summary: dict[str, Any] = {}
    for name in metric_names:
        summary[name] = app.aggregate_metrics(name)
    return summary


def merge_metrics_reports(*reports: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple metrics reports into a combined report.

    Each report is expected to be the output of MetricsCollector.export_metrics_report().
    """
    combined: dict[str, Any] = {"namespaces": [], "metrics": {}}
    for report in reports:
        ns = report.get("namespace", "unknown")
        combined["namespaces"].append(ns)
        for metric_name, metric_data in report.get("metrics", {}).items():
            key = f"{ns}.{metric_name}"
            combined["metrics"][key] = metric_data
    return combined


def reset_and_verify(app: AppManager) -> bool:
    """Reset metrics and verify they are cleared."""
    app.reset_metrics()
    all_metrics = app.get_all_metrics()
    return len(all_metrics) == 0


def get_metric_tags(app: AppManager, name: str) -> dict[str, str]:
    """Get the tags associated with a metric via the AppManager."""
    full_name = f"{app.metrics_namespace}.{name}"
    return dict(app._metrics_collector._metrics_tags.get(full_name, {}))
