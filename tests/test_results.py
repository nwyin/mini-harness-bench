import tempfile
from pathlib import Path

from mhb.reporting.results import read_results, write_results


def test_write_read_roundtrip():
    data = {
        "run_id": "test-123",
        "agent": "oracle",
        "model": "none",
        "tasks": {
            "task-a": {"correctness": 1.0, "tests_passed": 3, "tests_total": 3},
        },
        "summary": {"mean_correctness": 1.0},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "results.json"
        write_results(data, path)
        loaded = read_results(path)
        assert loaded["run_id"] == "test-123"
        assert loaded["tasks"]["task-a"]["correctness"] == 1.0


def test_write_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "deep" / "nested" / "results.json"
        write_results({"test": True}, path)
        assert path.exists()
