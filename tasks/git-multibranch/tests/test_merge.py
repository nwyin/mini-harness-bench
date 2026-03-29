import subprocess


def read_file(path):
    with open(path) as f:
        return f.read()


def test_on_main_branch():
    """After merging, we should be on the main branch."""
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    assert result.stdout.strip() == "main"


def test_no_conflict_markers():
    """No conflict markers should remain in any file."""
    for path in ["app.py", "config.py", "README.md"]:
        content = read_file(path)
        assert "<<<<<<<" not in content, f"Conflict marker found in {path}"
        assert ">>>>>>>" not in content, f"Conflict marker found in {path}"
        assert "=======" not in content, f"Conflict marker found in {path}"


def test_app_has_authenticate():
    """app.py should contain the authenticate function from feature-auth."""
    content = read_file("app.py")
    assert "def authenticate(" in content


def test_app_has_logging():
    """app.py should contain the setup_logging function from feature-logging."""
    content = read_file("app.py")
    assert "def setup_logging(" in content


def test_app_has_config_functions():
    """app.py should contain load_config and validate_config from feature-config."""
    content = read_file("app.py")
    assert "def load_config(" in content
    assert "def validate_config(" in content


def test_config_has_all_values():
    """config.py should contain config values from all branches."""
    content = read_file("config.py")
    assert "AUTH_ENABLED" in content
    assert "SESSION_TIMEOUT" in content
    assert "LOG_LEVEL" in content
    assert "LOG_FORMAT" in content
    assert "CONFIG_PATH" in content
    assert "RELOAD_INTERVAL" in content


def test_readme_has_all_sections():
    """README.md should contain sections from all branches."""
    content = read_file("README.md")
    assert "## Authentication" in content
    assert "## Logging" in content
    assert "## Configuration" in content


def test_readme_sections_alphabetical():
    """README.md sections should be in alphabetical order."""
    content = read_file("README.md")
    auth_pos = content.index("## Authentication")
    config_pos = content.index("## Configuration")
    logging_pos = content.index("## Logging")
    assert auth_pos < config_pos < logging_pos, "Sections should be in alphabetical order"
