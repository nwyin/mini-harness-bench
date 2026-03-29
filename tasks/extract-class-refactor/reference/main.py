"""Main application entry point that uses AppManager and MetricsCollector."""

from __future__ import annotations

from metrics import MetricsCollector
from monolith import AppManager


def run_processing_pipeline(app: AppManager, data: list[dict]) -> dict:
    """Run a data processing pipeline, recording metrics along the way."""
    app.info("Starting processing pipeline", item_count=len(data))

    processed = 0
    errors = 0
    for item in data:
        try:
            value = item.get("value", 0)
            if not isinstance(value, (int, float)):
                raise ValueError(f"Invalid value: {value}")
            app.record_metric("item_value", float(value))
            processed += 1
        except (ValueError, TypeError) as exc:
            app.error(f"Failed to process item: {exc}", item=item)
            errors += 1

    app.record_metric("processed_count", float(processed))
    app.record_metric("error_count", float(errors))
    app.info("Pipeline complete", processed=processed, errors=errors)

    return {"processed": processed, "errors": errors}


def generate_summary(app: AppManager) -> dict:
    """Generate a summary report from the AppManager metrics."""
    report = app.export_metrics_report()
    log_count = len(app.get_logs())
    error_count = len(app.get_logs("ERROR"))
    return {
        "metrics_report": report,
        "total_log_entries": log_count,
        "error_log_entries": error_count,
        "health": app.health_check(),
    }


def create_standalone_collector(namespace: str) -> MetricsCollector:
    """Create a standalone MetricsCollector for independent metrics collection."""
    return MetricsCollector(namespace=namespace)


def collect_batch_metrics(namespace: str, values: list[float]) -> dict:
    """Collect metrics for a batch of values and return the report."""
    collector = create_standalone_collector(namespace)
    for v in values:
        collector.record_metric("batch_value", v)
    agg = collector.aggregate_metrics("batch_value")
    report = collector.export_metrics_report()
    return {"aggregation": agg, "report": report}
