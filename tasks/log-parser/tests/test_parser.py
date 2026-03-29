import os
import sys

import pytest

# Add the workspace to path so we can import parser
sys.path.insert(0, os.getcwd())


def load_test_log(name):
    """Load a test log file from the hidden test data directory."""
    test_data_dir = os.path.join(os.path.dirname(__file__), "data")
    with open(os.path.join(test_data_dir, name)) as f:
        return f.read()


@pytest.fixture
def parse_log():
    from parser import parse_log

    return parse_log


def test_basic_log_entry_count(parse_log):
    """Basic log should produce correct number of entries."""
    entries = parse_log(load_test_log("test_basic.log"))
    assert len(entries) == 5


def test_basic_log_types(parse_log):
    """Basic log entries should have correct types."""
    entries = parse_log(load_test_log("test_basic.log"))
    types = [e["type"] for e in entries]
    assert types.count("standard") == 3
    assert types.count("request") == 2


def test_basic_request_fields(parse_log):
    """Request entries should have HTTP-specific fields."""
    entries = parse_log(load_test_log("test_basic.log"))
    requests = [e for e in entries if e["type"] == "request"]
    get_req = requests[0]
    assert get_req["method"] == "GET"
    assert get_req["path"] == "/api/status"
    assert get_req["status_code"] == 200
    assert get_req["response_time_ms"] == 5


def test_error_traceback(parse_log):
    """Error entries with tracebacks should capture them."""
    entries = parse_log(load_test_log("test_errors.log"))
    errors = [e for e in entries if e["type"] == "error"]
    assert len(errors) == 2
    assert errors[0]["traceback"] == "AuthenticationError: invalid credentials"
    assert errors[1]["traceback"] == "TimeoutError: query exceeded 30s limit"


def test_error_log_levels(parse_log):
    """All entry levels should be correct."""
    entries = parse_log(load_test_log("test_errors.log"))
    levels = [e["level"] for e in entries]
    assert "CRITICAL" in levels
    assert levels.count("ERROR") == 2


def test_timestamp_format(parse_log):
    """Timestamps should be in ISO format with T separator."""
    entries = parse_log(load_test_log("test_basic.log"))
    for entry in entries:
        assert "T" in entry["timestamp"]
        assert entry["timestamp"].count("-") == 2
        assert entry["timestamp"].count(":") == 2


def test_mixed_log_skips_garbage(parse_log):
    """Garbage lines should be skipped without error."""
    entries = parse_log(load_test_log("test_mixed.log"))
    # The garbage line should be skipped; 10 valid lines remain
    assert len(entries) == 9


def test_mixed_http_methods(parse_log):
    """Various HTTP methods should be parsed correctly."""
    entries = parse_log(load_test_log("test_mixed.log"))
    requests = [e for e in entries if e["type"] == "request"]
    methods = {e["method"] for e in requests}
    assert "GET" in methods
    assert "PUT" in methods
    assert "DELETE" in methods
    assert "POST" in methods
