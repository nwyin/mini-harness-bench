"""Application configuration module.

Provides a simple key-value configuration store.
Uses a class-based approach to avoid shared module-level state.
"""

from __future__ import annotations

from typing import Any


class Config:
    """Configuration store instance."""

    def __init__(self):
        self._state: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._state[key] = value

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values."""
        return dict(self._state)

    def reset(self) -> None:
        """Reset configuration to empty state."""
        self._state.clear()

    def load_defaults(self) -> None:
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
            if k not in self._state:
                self._state[k] = v


# Module-level convenience functions that delegate to a default instance.
# These preserve the original API for backward compatibility.
_default = Config()


def get(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    return _default.get(key, default)


def set(key: str, value: Any) -> None:  # noqa: A001
    """Set a configuration value."""
    _default.set(key, value)


def get_all() -> dict[str, Any]:
    """Get all configuration values."""
    return _default.get_all()


def reset() -> None:
    """Reset configuration to empty state."""
    _default.reset()


def load_defaults() -> None:
    """Load default configuration values."""
    _default.load_defaults()
