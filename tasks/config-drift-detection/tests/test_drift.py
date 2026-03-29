"""Tests for config-drift-detection task."""

import json
import os
import subprocess
import sys
from pathlib import Path

_pp = os.environ.get("PYTHONPATH")
WORKSPACE = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"
_task_dir = os.environ.get("MHB_TASK_DIR")
TEST_DATA = Path(_task_dir) / "tests" / "data" if _task_dir else Path(__file__).resolve().parent / "data"


def _run_detect(expected_dir: str, deployed_dir: str) -> dict:
    """Run detect_drift.py with the given directories and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "detect_drift.py"), expected_dir, deployed_dir],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
        timeout=30,
    )
    assert result.returncode == 0, f"detect_drift.py failed:\n{result.stderr}"
    return json.loads(result.stdout)


def test_workspace_example():
    """Detect drifts in the workspace example configs."""
    report = _run_detect(str(WORKSPACE / "expected"), str(WORKSPACE / "deployed"))
    drifts = report["drifts"]
    # At minimum, database pool_size, replicas, cache ttl missing, cache debug added
    drift_types = {(d["file"], d.get("path", ""), d["type"]) for d in drifts}
    assert ("database.json", "connection.pool_size", "value_changed") in drift_types
    assert ("cache.json", "ttl_seconds", "key_missing_in_deployed") in drift_types


def test_value_changed_drift():
    """Detect value_changed drifts in hidden test data set1."""
    report = _run_detect(str(TEST_DATA / "set1" / "expected"), str(TEST_DATA / "set1" / "deployed"))
    drifts = report["drifts"]
    value_changes = [d for d in drifts if d["type"] == "value_changed"]
    paths = {d["path"] for d in value_changes}
    assert "settings.debug" in paths
    assert "settings.log_level" in paths
    assert "settings.max_workers" in paths


def test_key_missing_drift():
    """Detect keys present in expected but missing from deployed."""
    report = _run_detect(str(TEST_DATA / "set1" / "expected"), str(TEST_DATA / "set1" / "deployed"))
    drifts = report["drifts"]
    missing = [d for d in drifts if d["type"] == "key_missing_in_deployed"]
    paths = {d["path"] for d in missing}
    assert "features.metrics" in paths


def test_file_missing_drift():
    """Detect file missing in deployed (secrets.json)."""
    report = _run_detect(str(TEST_DATA / "set1" / "expected"), str(TEST_DATA / "set1" / "deployed"))
    drifts = report["drifts"]
    file_missing = [d for d in drifts if d["type"] == "file_missing_in_deployed"]
    files = {d["file"] for d in file_missing}
    assert "secrets.json" in files


def test_no_drift_identical_files():
    """Identical files should produce no drifts for that file."""
    report = _run_detect(str(TEST_DATA / "set2" / "expected"), str(TEST_DATA / "set2" / "deployed"))
    drifts = report["drifts"]
    single_drifts = [d for d in drifts if d["file"] == "single.json"]
    assert len(single_drifts) == 0


def test_file_added_in_deployed():
    """Detect files that exist in deployed but not in expected."""
    report = _run_detect(str(TEST_DATA / "set2" / "expected"), str(TEST_DATA / "set2" / "deployed"))
    drifts = report["drifts"]
    added = [d for d in drifts if d["type"] == "file_added_in_deployed"]
    files = {d["file"] for d in added}
    assert "extra.json" in files


def test_summary_counts():
    """Summary must have correct counts."""
    report = _run_detect(str(TEST_DATA / "set1" / "expected"), str(TEST_DATA / "set1" / "deployed"))
    summary = report["summary"]
    assert summary["total_files_checked"] == 2  # app.json + secrets.json
    assert summary["files_with_drifts"] == 2
    assert summary["total_drifts"] >= 4  # at least debug, log_level, max_workers, metrics, secrets.json


def test_report_structure():
    """Report must have the correct top-level structure."""
    report = _run_detect(str(WORKSPACE / "expected"), str(WORKSPACE / "deployed"))
    assert "drifts" in report
    assert "summary" in report
    assert isinstance(report["drifts"], list)
    assert "total_files_checked" in report["summary"]
    assert "files_with_drifts" in report["summary"]
    assert "total_drifts" in report["summary"]
