#!/bin/bash
set -e

cd "$TASK_WORKSPACE"

# Initialize git repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Create initial files on main
cat > app.py << 'PYEOF'
"""Application module."""


def hello():
    """Return a greeting."""
    return "Hello, World!"
PYEOF

cat > config.py << 'PYEOF'
"""Configuration module."""

APP_NAME = "myapp"
VERSION = "1.0.0"
PYEOF

cat > README.md << 'MDEOF'
# MyApp

A sample application.
MDEOF

git add -A
git commit -m "Initial commit"

# Create feature-auth branch
git checkout -b feature-auth
cat > app.py << 'PYEOF'
"""Application module."""


def hello():
    """Return a greeting."""
    return "Hello, World!"


def authenticate(username, password):
    """Authenticate a user."""
    if not username or not password:
        raise ValueError("Username and password are required")
    return {"user": username, "authenticated": True}


def get_user_roles(username):
    """Get roles for a user."""
    default_roles = ["reader"]
    if username == "admin":
        return ["admin", "writer", "reader"]
    return default_roles
PYEOF

cat > config.py << 'PYEOF'
"""Configuration module."""

APP_NAME = "myapp"
VERSION = "1.0.0"
AUTH_ENABLED = True
SESSION_TIMEOUT = 3600
PYEOF

cat > README.md << 'MDEOF'
# MyApp

A sample application.

## Authentication

This app supports user authentication with role-based access control.
MDEOF

git add -A
git commit -m "Add authentication features"

# Create feature-logging branch from main
git checkout main
git checkout -b feature-logging
cat > app.py << 'PYEOF'
"""Application module."""


def hello():
    """Return a greeting."""
    return "Hello, World!"


def setup_logging(level="INFO"):
    """Configure application logging."""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    if level not in valid_levels:
        raise ValueError(f"Invalid log level: {level}")
    return {"level": level, "configured": True}


def log_request(method, path):
    """Log an incoming request."""
    return f"[REQUEST] {method} {path}"
PYEOF

cat > config.py << 'PYEOF'
"""Configuration module."""

APP_NAME = "myapp"
VERSION = "1.0.0"
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
PYEOF

cat > README.md << 'MDEOF'
# MyApp

A sample application.

## Logging

Structured logging with configurable log levels and format strings.
MDEOF

git add -A
git commit -m "Add logging features"

# Create feature-config branch from main
git checkout main
git checkout -b feature-config
cat > app.py << 'PYEOF'
"""Application module."""


def hello():
    """Return a greeting."""
    return "Hello, World!"


def load_config(path):
    """Load configuration from a file path."""
    import json
    with open(path) as f:
        return json.load(f)


def validate_config(config):
    """Validate configuration dictionary."""
    required_keys = ["app_name", "version"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing config keys: {missing}")
    return True
PYEOF

cat > config.py << 'PYEOF'
"""Configuration module."""

APP_NAME = "myapp"
VERSION = "1.0.0"
CONFIG_PATH = "/etc/myapp/config.json"
RELOAD_INTERVAL = 300
PYEOF

cat > README.md << 'MDEOF'
# MyApp

A sample application.

## Configuration

Dynamic configuration loading from JSON files with validation and hot-reload.
MDEOF

git add -A
git commit -m "Add configuration management features"

# Return to main
git checkout main
