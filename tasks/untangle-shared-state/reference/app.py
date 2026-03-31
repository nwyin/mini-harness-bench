"""Application entry point that ties config, cache, and handlers together.

Provides the App class that initializes config and processes requests.
Each App instance gets its own Config, Cache, and Handlers — no shared state.
"""

from __future__ import annotations

from typing import Any

from cache import Cache
from handlers import Handlers

from config import Config


class App:
    """Main application class."""

    def __init__(self, custom_config: dict[str, Any] | None = None):
        """Initialize the application.

        Each App instance gets its own isolated configuration and cache.
        """
        self._config = Config()
        self._config.load_defaults()
        if custom_config:
            for k, v in custom_config.items():
                self._config.set(k, v)
        self._cache = Cache(self._config)
        self._handlers = Handlers(self._config, self._cache)

    def process_request(self, request: dict) -> dict:
        """Process an incoming request."""
        req_type = request.get("type")
        action = request.get("action", "")

        if req_type == "user":
            user_id = request.get("user_id")
            if not user_id:
                return {"status": "error", "message": "Missing user_id"}
            return self._handlers.handle_user_request(user_id, action, request.get("payload"))
        elif req_type == "admin":
            return self._handlers.handle_admin_request(action, request.get("payload"))
        else:
            return {"status": "error", "message": f"Unknown request type: {req_type}"}

    def seed_users(self, users: dict[str, dict]) -> None:
        """Seed user data into config (for testing)."""
        for user_id, profile in users.items():
            self._config.set(f"user:{user_id}", profile)

    def get_config(self, key: str) -> Any:
        """Get a configuration value."""
        return self._config.get(key)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config.set(key, value)
