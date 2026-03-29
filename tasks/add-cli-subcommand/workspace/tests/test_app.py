import json
import subprocess
import sys


def run_app(*args):
    """Run app.py with given arguments and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "app.py", *args],
        capture_output=True,
        text=True,
    )


def test_existing_init_still_works():
    """The init subcommand must not be broken."""
    result = run_app("init", "--name", "myproject")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["action"] == "init"
    assert data["project_name"] == "myproject"


def test_existing_status_still_works():
    """The status subcommand must not be broken."""
    result = run_app("status")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["action"] == "status"


def test_deploy_staging():
    """Deploy to staging with a version."""
    result = run_app("deploy", "--env", "staging", "--version", "1.2.3")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["action"] == "deploy"
    assert data["environment"] == "staging"
    assert data["version"] == "1.2.3"
    assert data["dry_run"] is False


def test_deploy_production_requires_confirmation():
    """Deploy to production without --dry-run should include confirmation_required."""
    result = run_app("deploy", "--env", "production", "--version", "2.0.0")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["environment"] == "production"
    assert data["confirmation_required"] is True


def test_deploy_production_dry_run():
    """Deploy to production with --dry-run should NOT include confirmation_required."""
    result = run_app("deploy", "--env", "production", "--version", "2.0.0", "--dry-run")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["dry_run"] is True
    assert "confirmation_required" not in data


def test_deploy_missing_env():
    """Deploy without --env should fail."""
    result = run_app("deploy", "--version", "1.0.0")
    assert result.returncode != 0


def test_deploy_missing_version():
    """Deploy without --version should fail."""
    result = run_app("deploy", "--env", "staging")
    assert result.returncode != 0


def test_deploy_invalid_env():
    """Deploy with invalid --env value should fail."""
    result = run_app("deploy", "--env", "development", "--version", "1.0.0")
    assert result.returncode != 0
