"""Tests for dockerfile-to-shell task."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_pp = os.environ.get("PYTHONPATH")
WORKSPACE = Path(_pp) if _pp else Path(__file__).resolve().parent.parent / "workspace"


@pytest.fixture(scope="module")
def run_setup():
    """Run setup.sh once before all tests in this module."""
    setup_sh = WORKSPACE / "setup.sh"
    if not setup_sh.exists():
        pytest.skip("setup.sh not found")

    result = subprocess.run(
        ["bash", str(setup_sh)],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PATH": os.environ["PATH"]},
    )
    assert result.returncode == 0, f"setup.sh failed:\n{result.stderr}"
    return result


def test_setup_sh_exists():
    """setup.sh must exist."""
    assert (WORKSPACE / "setup.sh").exists()


def test_directory_structure(run_setup):
    """Required directories must exist."""
    for dirname in ["src", "config", "data", "logs"]:
        assert (WORKSPACE / dirname).is_dir(), f"Directory {dirname}/ not found"


def test_health_json(run_setup):
    """health.json must exist with correct content."""
    health_path = WORKSPACE / "health.json"
    assert health_path.exists(), "health.json not found"
    data = json.loads(health_path.read_text())
    assert data["status"] == "ok"
    assert data["version"] == "2.1.0"


def test_env_manifest(run_setup):
    """env_manifest.json must contain all Dockerfile ENV variables."""
    manifest_path = WORKSPACE / ".env_manifest.json"
    assert manifest_path.exists(), ".env_manifest.json not found"
    manifest = json.loads(manifest_path.read_text())

    expected_vars = {
        "APP_NAME": "warehouse-api",
        "APP_VERSION": "2.1.0",
        "APP_ENV": "production",
        "LOG_LEVEL": "warning",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "CACHE_TTL": "3600",
        "MAX_WORKERS": "4",
    }
    for key, value in expected_vars.items():
        assert key in manifest, f"ENV var {key} missing from manifest"
        assert manifest[key] == value, f"ENV var {key}: expected {value!r}, got {manifest[key]!r}"


def test_pkg_manifest(run_setup):
    """pkg_manifest.json must list the required packages."""
    manifest_path = WORKSPACE / ".pkg_manifest.json"
    assert manifest_path.exists(), ".pkg_manifest.json not found"
    manifest = json.loads(manifest_path.read_text())

    required_packages = ["pydantic", "httpx", "python-dotenv", "structlog"]
    for pkg in required_packages:
        found = any(pkg.lower() == k.lower() for k in manifest)
        assert found, f"Package {pkg} not in package manifest"


def test_application_files(run_setup):
    """Application source and config files must be in the right locations."""
    assert (WORKSPACE / "src" / "main.py").exists()
    assert (WORKSPACE / "config" / "settings.json").exists()
    assert (WORKSPACE / "config" / "logging.yaml").exists()


def test_requirements_present(run_setup):
    """requirements.txt must be present."""
    assert (WORKSPACE / "requirements.txt").exists()


def test_python_packages_importable(run_setup):
    """Required Python packages must be importable."""
    result = subprocess.run(
        [sys.executable, "-c", "import pydantic; import httpx; import dotenv; import structlog; print('ok')"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
        timeout=30,
    )
    assert result.stdout.strip() == "ok", f"Import failed:\n{result.stderr}"
