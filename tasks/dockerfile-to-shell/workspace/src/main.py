"""Main application entry point."""

import os


def get_app_info():
    return {
        "name": os.environ.get("APP_NAME", "unknown"),
        "version": os.environ.get("APP_VERSION", "0.0.0"),
        "env": os.environ.get("APP_ENV", "development"),
    }


if __name__ == "__main__":
    info = get_app_info()
    print(f"Starting {info['name']} v{info['version']} ({info['env']})")
