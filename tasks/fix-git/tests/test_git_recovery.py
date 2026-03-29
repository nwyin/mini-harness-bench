import subprocess


def _run_git(*args):
    result = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def test_branch_exists():
    """The feature-auth branch should exist."""
    out, rc = _run_git("branch", "--list", "feature-auth")
    assert "feature-auth" in out, "Branch 'feature-auth' not found"


def test_branch_has_auth_commit():
    """The branch should contain a commit with 'Add authentication module'."""
    out, rc = _run_git("log", "feature-auth", "--oneline", "-1")
    assert rc == 0, "Cannot read feature-auth log"
    assert "Add authentication module" in out


def test_auth_py_exists_on_branch():
    """The auth.py file should exist on the feature-auth branch."""
    out, rc = _run_git("show", "feature-auth:auth.py")
    assert rc == 0, "auth.py not found on feature-auth branch"
    assert "AuthModule" in out


def test_no_new_commits_on_main():
    """Main branch should not have new commits (only initial)."""
    out, _ = _run_git("log", "--oneline")
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1, f"Expected 1 commit on main, got {len(lines)}"
