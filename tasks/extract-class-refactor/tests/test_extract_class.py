"""Tests for the extract-class-refactor task."""

import os
import sys
from pathlib import Path


def test_metrics_module_exists():
    """metrics.py must exist as a separate module."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        import importlib

        spec = importlib.util.find_spec("metrics")
        assert spec is not None, "metrics.py module not found"
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_metrics_collector_class():
    """MetricsCollector class must exist in metrics.py with namespace param."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from metrics import MetricsCollector

        mc = MetricsCollector(namespace="test")
        assert mc.namespace == "test"
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_metrics_collector_record_and_get():
    """MetricsCollector must support record_metric and get_metric."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from metrics import MetricsCollector

        mc = MetricsCollector(namespace="ns")
        mc.record_metric("latency", 1.5)
        mc.record_metric("latency", 2.5)
        vals = mc.get_metric("latency")
        assert vals == [1.5, 2.5]
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_metrics_collector_aggregate():
    """MetricsCollector must support aggregate_metrics."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from metrics import MetricsCollector

        mc = MetricsCollector(namespace="agg")
        mc.record_metric("val", 10.0)
        mc.record_metric("val", 20.0)
        mc.record_metric("val", 30.0)
        agg = mc.aggregate_metrics("val")
        assert agg["min"] == 10.0
        assert agg["max"] == 30.0
        assert agg["mean"] == 20.0
        assert agg["count"] == 3
        assert agg["sum"] == 60.0
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_metrics_collector_export_report():
    """MetricsCollector must support export_metrics_report."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from metrics import MetricsCollector

        mc = MetricsCollector(namespace="rpt")
        mc.record_metric("x", 5.0, tags={"env": "prod"})
        report = mc.export_metrics_report()
        assert report["namespace"] == "rpt"
        assert "x" in report["metrics"]
        assert report["metrics"]["x"]["values"] == [5.0]
        assert report["metrics"]["x"]["tags"]["env"] == "prod"
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_app_manager_delegates_to_collector():
    """AppManager must still work for metrics by delegating to MetricsCollector."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from monolith import AppManager

        app = AppManager("test-app", metrics_namespace="app")
        app.record_metric("req_count", 1.0)
        app.record_metric("req_count", 2.0)
        assert app.get_metric("req_count") == [1.0, 2.0]
        agg = app.aggregate_metrics("req_count")
        assert agg["count"] == 2

        report = app.export_metrics_report()
        assert report["namespace"] == "app"

        app.reset_metrics()
        assert app.get_all_metrics() == {}
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_main_standalone_collector():
    """main.py must use MetricsCollector for standalone collection."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from main import collect_batch_metrics, create_standalone_collector
        from metrics import MetricsCollector

        collector = create_standalone_collector("standalone")
        assert isinstance(collector, MetricsCollector)

        result = collect_batch_metrics("batch", [1.0, 2.0, 3.0])
        assert result["aggregation"]["count"] == 3
        assert result["aggregation"]["mean"] == 2.0
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]


def test_utils_still_work():
    """utils.py functions must still work with the refactored code."""
    _pp = os.environ.get("PYTHONPATH")
    workspace = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        from monolith import AppManager
        from utils import build_metrics_summary, reset_and_verify, timed_operation

        app = AppManager("util-test", metrics_namespace="ut")
        timed_operation(app, "db_query", 42.5)
        summary = build_metrics_summary(app, ["op.db_query.duration_ms"])
        assert summary["op.db_query.duration_ms"]["count"] == 1
        assert summary["op.db_query.duration_ms"]["sum"] == 42.5

        assert reset_and_verify(app) is True
    finally:
        sys.path.pop(0)
        for mod_name in list(sys.modules):
            if mod_name in ("metrics", "monolith", "main", "utils"):
                del sys.modules[mod_name]
