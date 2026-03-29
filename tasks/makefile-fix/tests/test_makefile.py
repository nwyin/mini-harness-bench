"""Tests for makefile-fix task."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_pp = os.environ.get("PYTHONPATH")
WORKSPACE = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"


@pytest.fixture(autouse=True)
def clean_build():
    """Clean build directory before and after each test."""
    build_dir = WORKSPACE / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    yield
    if build_dir.exists():
        shutil.rmtree(build_dir)


def _run_make(target: str = "all") -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", target],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_make_all_succeeds():
    """make all must exit 0."""
    result = _run_make("all")
    assert result.returncode == 0, f"make all failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"


def test_output_txt_exists():
    """build/output.txt must be created."""
    _run_make("all")
    assert (WORKSPACE / "build" / "output.txt").exists()


def test_config_json_exists():
    """build/config.json must be created with correct content."""
    _run_make("all")
    config_path = WORKSPACE / "build" / "config.json"
    assert config_path.exists(), "build/config.json not found"
    config = json.loads(config_path.read_text())
    assert config["version"] == "1.0.0"
    assert "features" in config


def test_lint_report_exists():
    """build/lint_report.txt must be created."""
    _run_make("all")
    lint_path = WORKSPACE / "build" / "lint_report.txt"
    assert lint_path.exists()
    content = lint_path.read_text()
    assert "Lint report" in content
    assert "All checks passed" in content


def test_templates_exist():
    """build/templates.txt must be created."""
    _run_make("all")
    templates_path = WORKSPACE / "build" / "templates.txt"
    assert templates_path.exists()
    content = templates_path.read_text()
    assert "Compiled templates" in content


def test_output_contains_all_sections():
    """build/output.txt must contain lint, config, and template sections."""
    _run_make("all")
    content = (WORKSPACE / "build" / "output.txt").read_text()
    assert "BUILD REPORT" in content
    assert "Lint Results" in content
    assert "Config" in content
    assert "Templates" in content
    assert "BUILD COMPLETE" in content


def test_clean_removes_build():
    """make clean must remove the build directory or all generated files."""
    _run_make("all")
    assert (WORKSPACE / "build" / "output.txt").exists()
    _run_make("clean")
    build_dir = WORKSPACE / "build"
    if build_dir.exists():
        generated = list(build_dir.glob("*.txt")) + list(build_dir.glob("*.json"))
        assert len(generated) == 0, f"Generated files remain after clean: {generated}"


def test_make_is_idempotent():
    """Running make all twice should succeed both times."""
    result1 = _run_make("all")
    assert result1.returncode == 0
    result2 = _run_make("all")
    assert result2.returncode == 0
