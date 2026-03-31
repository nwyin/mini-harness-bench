"""Application entry point that ties config, cache, and handlers together.

Provides the App class that initializes config and processes requests.
"""

from __future__ import annotations

from typing import Any

import handlers

import config


class App:
    """Main application class."""

    def __init__(self, custom_config: dict[str, Any] | None = None):
        """Initialize the application.

        Loads default config, then applies any custom config overrides.
        """
        config.load_defaults()
        if custom_config:
            for k, v in custom_config.items():
                config.set(k, v)

    def process_request(self, request: dict) -> dict:
        """Process an incoming request.

        Request format:
        {
            "type": "user" | "admin",
            "user_id": str (for user requests),
            "action": str,
            "payload": dict (optional)
        }
        """
        req_type = request.get("type")
        action = request.get("action", "")

        if req_type == "user":
            user_id = request.get("user_id")
            if not user_id:
                return {"status": "error", "message": "Missing user_id"}
            return handlers.handle_user_request(user_id, action, request.get("payload"))
        elif req_type == "admin":
            return handlers.handle_admin_request(action, request.get("payload"))
        else:
            return {"status": "error", "message": f"Unknown request type: {req_type}"}

    def seed_users(self, users: dict[str, dict]) -> None:
        """Seed user data into config (for testing)."""
        for user_id, profile in users.items():
            config.set(f"user:{user_id}", profile)

    def get_config(self, key: str) -> Any:
        """Get a configuration value."""
        return config.get(key)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        config.set(key, value)
