"""Tests for the application.

These tests pass individually but fail when run together due to shared state.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure workspace is on the path
ws = str(Path(__file__).resolve().parent.parent)
if ws not in sys.path:
    sys.path.insert(0, ws)

from app import App  # noqa: E402


def test_basic_request():
    """App should handle a basic user profile request."""
    app = App()
    app.seed_users({"alice": {"name": "Alice", "level": 5, "activity_count": 100}})

    result = app.process_request({"type": "user", "user_id": "alice", "action": "get_profile"})
    assert result["status"] == "ok"
    assert result["profile"]["name"] == "Alice"


def test_custom_config():
    """App with custom config should use those values."""
    app = App(custom_config={"timeout_sec": 60, "debug": True})
    assert app.get_config("timeout_sec") == 60
    assert app.get_config("debug") is True
    # Default values should still be present
    assert app.get_config("app_name") == "myapp"


def test_default_config_only():
    """A fresh App should have only default config values."""
    app = App()
    assert app.get_config("debug") is False
    assert app.get_config("timeout_sec") == 30
    assert app.get_config("max_connections") == 100


def test_no_stale_users():
    """A fresh App should not have user data from elsewhere."""
    app = App()
    # If alice was seeded by a previous test, this will incorrectly succeed
    result = app.process_request({"type": "user", "user_id": "alice", "action": "get_profile"})
    assert result["status"] == "error", (
        f"alice should not exist in a fresh App, got status={result['status']} — user data is leaking between App instances"
    )


def test_user_update_invalidates_cache():
    """Updating a user should invalidate their cache."""
    app = App()
    app.seed_users({"carol": {"name": "Carol", "level": 2, "activity_count": 30}})

    # First request caches the profile
    r1 = app.process_request({"type": "user", "user_id": "carol", "action": "get_profile"})
    assert r1["profile"]["name"] == "Carol"

    # Update the profile
    app.process_request(
        {
            "type": "user",
            "user_id": "carol",
            "action": "update_profile",
            "payload": {"name": "Carol Updated"},
        }
    )

    # Next request should get the updated profile (not stale cache)
    r2 = app.process_request({"type": "user", "user_id": "carol", "action": "get_profile"})
    assert r2["profile"]["name"] == "Carol Updated"


def test_compute_score():
    """Score computation should work and cache results."""
    app = App()
    app.seed_users({"dave": {"name": "Dave", "level": 10, "activity_count": 200}})

    r1 = app.process_request(
        {
            "type": "user",
            "user_id": "dave",
            "action": "compute_score",
            "payload": {"multiplier": 2.0},
        }
    )
    assert r1["status"] == "ok"
    assert r1["source"] == "computed"
    assert r1["score"] == 400.0  # (200 * 10 * 2.0) / 10 = 400.0

    # Second request should come from cache
    r2 = app.process_request(
        {
            "type": "user",
            "user_id": "dave",
            "action": "compute_score",
            "payload": {"multiplier": 2.0},
        }
    )
    assert r2["source"] == "cache"
    assert r2["score"] == 400.0


def test_admin_clear_cache():
    """Admin clear_cache should work without errors."""
    app = App()
    app.seed_users({"eve": {"name": "Eve", "level": 1, "activity_count": 10}})
    app.process_request({"type": "user", "user_id": "eve", "action": "get_profile"})

    result = app.process_request({"type": "admin", "action": "clear_cache"})
    assert result["status"] == "ok"

    # After clearing cache, profile should come from "db" not cache
    r2 = app.process_request({"type": "user", "user_id": "eve", "action": "get_profile"})
    assert r2["source"] == "db"


def test_fresh_app_default_log_level():
    """A new App should always have log_level=INFO regardless of prior usage."""
    app = App()
    assert app.get_config("log_level") == "INFO", (
        f"Expected default 'INFO' but got '{app.get_config('log_level')}' — config state is leaking between App instances"
    )
