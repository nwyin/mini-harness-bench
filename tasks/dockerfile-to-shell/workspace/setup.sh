#!/bin/bash
set -e

# Environment configuration (from Dockerfile ENV directives)
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

# Create app directory structure (mirrors WORKDIR /app + RUN mkdir)
# Create in current directory to match final container state
mkdir -p src
mkdir -p config
mkdir -p data
mkdir -p logs

# Copy application code (COPY src/ /app/src/)
# Files are already in src/, so just ensure they exist
# (In container, these would be copied from build context)

# Copy config files (COPY config/settings.json and logging.yaml)
# Files are already in config/, so just ensure they exist

# Create health check file (RUN echo '{"status": "ok", "version": "2.1.0"}' > /app/health.json)
echo '{"status": "ok", "version": "2.1.0"}' > health.json

# requirements.txt is already present in current directory

# Install Python packages from requirements.txt
# Using pip install (or uv pip install if available)
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt
else
    pip install --no-cache-dir -r requirements.txt
fi

# Generate .env_manifest.json - list all environment variables and their values
cat > .env_manifest.json << 'EOF'
{
  "APP_NAME": "warehouse-api",
  "APP_VERSION": "2.1.0",
  "APP_ENV": "production",
  "LOG_LEVEL": "warning",
  "DB_HOST": "localhost",
  "DB_PORT": "5432",
  "CACHE_TTL": "3600",
  "MAX_WORKERS": "4",
  "PYTHONUNBUFFERED": "1",
  "PYTHONDONTWRITEBYTECODE": "1"
}
EOF

# Generate .pkg_manifest.json - list all pip-installed packages
# Get the list of installed packages in JSON format
python << 'PYTHON_SCRIPT'
import json
import subprocess

# Run pip list --format=json to get installed packages
result = subprocess.run(['pip', 'list', '--format', 'json'], capture_output=True, text=True)
packages = json.loads(result.stdout)

# Create a manifest with package names and versions
manifest = {}
for pkg in packages:
    manifest[pkg['name']] = pkg['version']

# Write to .pkg_manifest.json
with open('.pkg_manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
PYTHON_SCRIPT

echo "Setup complete!"
