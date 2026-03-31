"""Basic tests to verify the processor still works after cleanup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from processor import DataProcessor


def test_basic_process():
    """process() should work on simple data."""
    proc = DataProcessor()
    result = proc.process({"name": "test", "values": [1, 2, 3]})
    assert result["processed"] is True
    assert result["name"] == "test"


def test_process_with_format():
    """process() with html format should sanitize strings."""
    proc = DataProcessor()
    result = proc.process({"name": "<b>bold</b>", "format": "html"})
    assert result["processed"] is True
    assert "<b>" not in result["name"]
