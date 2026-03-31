"""Request handlers that use config and cache.

Processes incoming requests, applies business logic, and uses caching
for expensive computations.
"""

from __future__ import annotations

from cache import Cache, compute_cache_key

from config import Config


class Handlers:
    """Request handlers backed by a Config and Cache instance."""

    def __init__(self, cfg: Config, cache: Cache):
        self._cfg = cfg
        self._cache = cache

    def handle_user_request(self, user_id: str, action: str, payload: dict | None = None) -> dict:
        """Handle a user request."""
        if action == "get_profile":
            return self._get_profile(user_id)
        elif action == "update_profile":
            return self._update_profile(user_id, payload or {})
        elif action == "compute_score":
            return self._compute_score(user_id, payload or {})
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _get_profile(self, user_id: str) -> dict:
        cache_key = f"profile:{user_id}"
        cached = self._cache.cache_get(cache_key)
        if cached is not None:
            return {"status": "ok", "source": "cache", "profile": cached}

        profile = self._cfg.get(f"user:{user_id}", None)
        if profile is None:
            return {"status": "error", "message": f"User {user_id} not found"}

        self._cache.cache_set(cache_key, profile)
        return {"status": "ok", "source": "db", "profile": profile}

    def _update_profile(self, user_id: str, updates: dict) -> dict:
        profile = self._cfg.get(f"user:{user_id}", {})
        profile.update(updates)
        self._cfg.set(f"user:{user_id}", profile)
        self._cache.cache_delete(f"profile:{user_id}")
        return {"status": "ok", "profile": profile}

    def _compute_score(self, user_id: str, params: dict) -> dict:
        cache_key = compute_cache_key("score", user_id, params)
        cached = self._cache.cache_get(cache_key)
        if cached is not None:
            return {"status": "ok", "source": "cache", "score": cached}

        profile = self._cfg.get(f"user:{user_id}", None)
        if profile is None:
            return {"status": "error", "message": f"User {user_id} not found"}

        activity = profile.get("activity_count", 0)
        level = profile.get("level", 1)
        multiplier = params.get("multiplier", 1.0)
        score = round((activity * level * multiplier) / 10.0, 2)

        self._cache.cache_set(cache_key, score)
        return {"status": "ok", "source": "computed", "score": score}

    def handle_admin_request(self, action: str, payload: dict | None = None) -> dict:
        """Handle an admin request."""
        if action == "get_config":
            return {"status": "ok", "config": self._cfg.get_all()}
        elif action == "set_config":
            if not payload:
                return {"status": "error", "message": "No payload"}
            for k, v in payload.items():
                self._cfg.set(k, v)
            return {"status": "ok"}
        elif action == "clear_cache":
            self._cache.cache_clear()
            return {"status": "ok", "message": "Cache cleared"}
        elif action == "get_stats":
            return {"status": "ok", "stats": self._cache.cache_stats()}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}


# Module-level convenience functions for backward compatibility
import cache as _cache_module  # noqa: E402

import config as _config_module  # noqa: E402

_default_handlers = Handlers(_config_module._default, _cache_module._default_cache)


def handle_user_request(user_id: str, action: str, payload: dict | None = None) -> dict:
    return _default_handlers.handle_user_request(user_id, action, payload)


def handle_admin_request(action: str, payload: dict | None = None) -> dict:
    return _default_handlers.handle_admin_request(action, payload)
