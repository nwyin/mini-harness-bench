#!/bin/bash
set -euo pipefail

# Environment variables from Dockerfile ENV directives
export APP_NAME=warehouse-api
export APP_VERSION=2.1.0
export APP_ENV=production
export LOG_LEVEL=warning
export DB_HOST=localhost
export DB_PORT=5432
export CACHE_TTL=3600
export MAX_WORKERS=4
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Create directory structure (matching Dockerfile WORKDIR and RUN mkdir)
mkdir -p src config data logs

# Create health check file (matching Dockerfile RUN echo)
echo '{"status": "ok", "version": "2.1.0"}' > health.json

# Install Python packages from requirements.txt
pip install -r requirements.txt 2>/dev/null || uv pip install -r requirements.txt 2>/dev/null || true

# Generate environment manifest
python3 << 'PYEOF'
import json
import os

env_vars = {
    "APP_NAME": os.environ.get("APP_NAME", ""),
    "APP_VERSION": os.environ.get("APP_VERSION", ""),
    "APP_ENV": os.environ.get("APP_ENV", ""),
    "LOG_LEVEL": os.environ.get("LOG_LEVEL", ""),
    "DB_HOST": os.environ.get("DB_HOST", ""),
    "DB_PORT": os.environ.get("DB_PORT", ""),
    "CACHE_TTL": os.environ.get("CACHE_TTL", ""),
    "MAX_WORKERS": os.environ.get("MAX_WORKERS", ""),
    "PYTHONUNBUFFERED": os.environ.get("PYTHONUNBUFFERED", ""),
    "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE", ""),
}
with open(".env_manifest.json", "w") as f:
    json.dump(env_vars, f, indent=2, sort_keys=True)
PYEOF

# Generate package manifest
python3 << 'PYEOF'
import json
import importlib.metadata

packages = {}
for dist in importlib.metadata.distributions():
    name = dist.metadata["Name"]
    version = dist.metadata["Version"]
    packages[name.lower()] = version

with open(".pkg_manifest.json", "w") as f:
    json.dump(packages, f, indent=2, sort_keys=True)
PYEOF
