"""Hidden tests for dead-code-trap task."""

import base64
import json
import os
import sys
import zlib
from pathlib import Path


def _workspace():
    pp = os.environ.get("PYTHONPATH")
    if pp:
        return Path(pp)
    return Path(__file__).resolve().parent.parent / "workspace"


def _setup():
    ws = str(_workspace())
    if ws not in sys.path:
        sys.path.insert(0, ws)


def _cleanup():
    for mod_name in list(sys.modules):
        if mod_name in ("processor",):
            del sys.modules[mod_name]


def test_dead_code_removed():
    """_log_metrics, _retry_with_backoff, _compress_data should be removed."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()
        assert not hasattr(proc, "_log_metrics"), "_log_metrics is dead code and should be removed"
        assert not hasattr(proc, "_retry_with_backoff"), "_retry_with_backoff is dead code and should be removed"
        assert not hasattr(proc, "_compress_data"), "_compress_data is dead code and should be removed"
    finally:
        _cleanup()


def test_sanitize_html_exists():
    """_sanitize_html must still exist and work (called via getattr dispatch)."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()
        assert hasattr(proc, "_sanitize_html"), "_sanitize_html is reachable via getattr and must be kept"
        result = proc._sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    finally:
        _cleanup()


def test_sanitize_json_exists():
    """_sanitize_json must still exist and work (called via getattr dispatch)."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()
        assert hasattr(proc, "_sanitize_json"), "_sanitize_json is reachable via getattr and must be kept"
        result = proc._sanitize_json('hello "world"')
        assert '\\"' in result or "\\u0022" in result
    finally:
        _cleanup()


def test_decompress_exists():
    """_decompress_data must still exist and work (referenced in HANDLERS)."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()
        assert hasattr(proc, "_decompress_data"), "_decompress_data is reachable via HANDLERS and must be kept"
    finally:
        _cleanup()


def test_process_works():
    """process() produces correct output on basic data."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()
        result = proc.process({"name": "test-item", "values": [10, 20, 30]})
        assert result["processed"] is True
        assert result["name"] == "test-item"
        assert "values" in result
        # Values should be normalized (zero mean, unit variance)
        vals = result["values"]
        assert len(vals) == 3
        mean = sum(vals) / len(vals)
        assert abs(mean) < 1e-9, f"Normalized values should have zero mean, got {mean}"
    finally:
        _cleanup()


def test_transform_with_sanitize():
    """transform with html/json format applies sanitization via getattr."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()

        # HTML sanitization
        html_result = proc.process(
            {
                "title": "<h1>Hello & World</h1>",
                "format": "html",
            }
        )
        assert "&lt;h1&gt;" in html_result["title"]
        assert "&amp;" in html_result["title"]

        # JSON sanitization
        json_result = proc.process(
            {
                "content": 'value with "quotes" and \\ backslash',
                "format": "json",
            }
        )
        assert '"' not in json_result["content"] or '\\"' in json_result["content"]
    finally:
        _cleanup()


def test_handler_dispatch():
    """HANDLERS dict dispatch works for decompress action."""
    _setup()
    try:
        from processor import DataProcessor

        proc = DataProcessor()

        # Create compressed payload
        payload = {"name": "decompressed-item", "status": "active"}
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        encoded = base64.b64encode(compressed).decode("ascii")

        result = proc.process(
            {
                "action": "decompress",
                "compressed": encoded,
            }
        )
        assert result["processed"] is True
        assert result["name"] == "decompressed-item"
        assert result["status"] == "active"
    finally:
        _cleanup()
