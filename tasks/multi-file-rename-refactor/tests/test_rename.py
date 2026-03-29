"""Tests for multi-file-rename-refactor task."""

import ast
import os
import sys
from pathlib import Path


def _workspace() -> Path:
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _add_workspace():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup_modules():
    for mod_name in list(sys.modules):
        if mod_name in (
            "processor",
            "pipeline",
            "runner",
            "config",
            "validators",
            "hooks",
            "registry",
            "cli",
        ):
            del sys.modules[mod_name]


def test_class_renamed_in_processor():
    """PipelineExecutor must be defined in processor.py; DataProcessor must not."""
    _add_workspace()
    try:
        from processor import PipelineExecutor

        pe = PipelineExecutor(name="test")
        assert pe.name == "test"
        assert hasattr(pe, "run")
        assert hasattr(pe, "add_step")
    finally:
        _cleanup_modules()


def test_no_dataprocessor_class_definition():
    """No file should define a class called DataProcessor."""
    ws = _workspace()
    for py_file in ws.glob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "DataProcessor":
                raise AssertionError(f"{py_file.name} still defines class DataProcessor")


def test_no_dataprocessor_in_imports():
    """No file should import DataProcessor."""
    ws = _workspace()
    for py_file in ws.glob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    actual_name = alias.name
                    assert actual_name != "DataProcessor", f"{py_file.name} still imports DataProcessor"


def test_pipeline_uses_pipeline_executor():
    """pipeline.py must import and use PipelineExecutor."""
    _add_workspace()
    try:
        from pipeline import create_pipeline

        p = create_pipeline("test", steps=[lambda d: d])
        from processor import PipelineExecutor

        assert isinstance(p, PipelineExecutor)
    finally:
        _cleanup_modules()


def test_runner_uses_pipeline_executor():
    """runner.py execute() must work with PipelineExecutor."""
    _add_workspace()
    try:
        from processor import PipelineExecutor
        from runner import execute

        pe = PipelineExecutor(name="runner-test")
        pe.add_step(lambda d: d)
        result = execute(pe, [{"a": 1}])
        assert result.output_count == 1
    finally:
        _cleanup_modules()


def test_config_creates_pipeline_executor():
    """config.py factory functions must return PipelineExecutor."""
    _add_workspace()
    try:
        from processor import PipelineExecutor

        from config import create_custom, create_from_preset, lowercase_keys

        p1 = create_from_preset("clean")
        assert isinstance(p1, PipelineExecutor)

        p2 = create_custom("custom", [lowercase_keys])
        assert isinstance(p2, PipelineExecutor)
    finally:
        _cleanup_modules()


def test_validators_accept_pipeline_executor():
    """validators.py must work with PipelineExecutor."""
    _add_workspace()
    try:
        from processor import PipelineExecutor
        from validators import validate_output, validate_processor

        pe = PipelineExecutor(name="val-test")
        errors = validate_processor(pe)
        assert any("at least one step" in e.lower() for e in errors)

        pe.add_step(lambda d: d)
        result = validate_output(pe, [{"x": 1}], expected_count=1)
        assert result["valid"] is True
    finally:
        _cleanup_modules()


def test_hooks_work_with_pipeline_executor():
    """hooks.py must work with PipelineExecutor."""
    _add_workspace()
    try:
        from hooks import HookRegistry, run_with_hooks
        from processor import PipelineExecutor

        pe = PipelineExecutor(name="hook-test")
        pe.add_step(lambda d: d)

        triggered = []
        registry = HookRegistry()
        registry.register("after_run", lambda proc, ctx: triggered.append(ctx))

        run_with_hooks(pe, [{"a": 1}], registry)
        assert len(triggered) == 1
        assert triggered[0]["output_count"] == 1
    finally:
        _cleanup_modules()


def test_repr_says_pipeline_executor():
    """repr() of the class must say PipelineExecutor, not DataProcessor."""
    _add_workspace()
    try:
        from processor import PipelineExecutor

        pe = PipelineExecutor(name="repr-test")
        r = repr(pe)
        assert "PipelineExecutor" in r
        assert "DataProcessor" not in r
    finally:
        _cleanup_modules()
