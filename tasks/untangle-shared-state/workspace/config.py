"""Application configuration module.

Provides a simple key-value configuration store.
"""

from __future__ import annotations

from typing import Any

# Module-level shared state
_state: dict[str, Any] = {}


def get(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    return _state.get(key, default)


def set(key: str, value: Any) -> None:  # noqa: A001
    """Set a configuration value."""
    _state[key] = value


def get_all() -> dict[str, Any]:
    """Get all configuration values."""
    return dict(_state)


def reset() -> None:
    """Reset configuration to empty state."""
    _state.clear()


def load_defaults() -> None:
    """Load default configuration values."""
    defaults = {
        "app_name": "myapp",
        "version": "1.0.0",
        "debug": False,
        "max_connections": 100,
        "timeout_sec": 30,
        "cache_enabled": True,
        "cache_ttl_sec": 300,
        "log_level": "INFO",
    }
    for k, v in defaults.items():
        if k not in _state:
            _state[k] = v
