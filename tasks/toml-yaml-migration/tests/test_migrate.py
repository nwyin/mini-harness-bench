import os
import subprocess
import sys

import pytest
import yaml

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


@pytest.fixture(autouse=True)
def run_migrate():
    """Run the migration script before tests."""
    result = subprocess.run([sys.executable, "migrate.py"], capture_output=True, text=True)
    assert result.returncode == 0, f"migrate.py failed: {result.stderr}"


def load_toml():
    with open("config.toml", "rb") as f:
        return tomllib.load(f)


def load_yaml():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def test_output_exists():
    assert os.path.exists("config.yaml")


def test_top_level_keys():
    data = load_yaml()
    assert "app" in data
    assert "database" in data
    assert "logging" in data
    assert "redis" in data
    assert "features" in data
    assert "monitoring" in data


def test_app_values():
    data = load_yaml()
    app = data["app"]
    assert app["name"] == "myservice"
    assert app["version"] == "2.4.1"
    assert app["debug"] is False
    assert app["max_connections"] == 100


def test_nested_tables():
    data = load_yaml()
    assert data["app"]["timeouts"]["connect"] == 5
    assert data["app"]["timeouts"]["read"] == 30
    assert data["database"]["replica"]["host"] == "db-replica.internal.corp"
    assert data["database"]["replica"]["read_only"] is True
    assert data["logging"]["file"]["path"] == "/var/log/myservice/app.log"


def test_lists_preserved():
    data = load_yaml()
    assert isinstance(data["app"]["allowed_hosts"], list)
    assert len(data["app"]["allowed_hosts"]) == 3
    assert "localhost" in data["app"]["allowed_hosts"]
    assert isinstance(data["logging"]["handlers"], list)
    assert set(data["logging"]["handlers"]) == {"console", "file", "syslog"}


def test_boolean_values():
    data = load_yaml()
    assert data["database"]["ssl"] is True
    assert data["features"]["enable_caching"] is True
    assert data["features"]["enable_metrics"] is False


def test_integer_values():
    data = load_yaml()
    assert data["database"]["port"] == 5432
    assert data["redis"]["port"] == 6379
    assert data["redis"]["db"] == 0
    assert data["monitoring"]["interval_seconds"] == 60


def test_full_structure_match():
    """The YAML output should match the TOML input exactly when both are loaded as dicts."""
    toml_data = load_toml()
    yaml_data = load_yaml()
    assert toml_data == yaml_data
