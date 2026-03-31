"""Request handlers that use config and cache.

Processes incoming requests, applies business logic, and uses caching
for expensive computations.
"""

from __future__ import annotations

import cache

import config


def handle_user_request(user_id: str, action: str, payload: dict | None = None) -> dict:
    """Handle a user request.

    Actions: get_profile, update_profile, compute_score
    """
    if action == "get_profile":
        return _get_profile(user_id)
    elif action == "update_profile":
        return _update_profile(user_id, payload or {})
    elif action == "compute_score":
        return _compute_score(user_id, payload or {})
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


def _get_profile(user_id: str) -> dict:
    """Get a user profile, with caching."""
    cache_key = f"profile:{user_id}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return {"status": "ok", "source": "cache", "profile": cached}

    # Simulate loading from a "database" (config-based for this example)
    profile = config.get(f"user:{user_id}", None)
    if profile is None:
        return {"status": "error", "message": f"User {user_id} not found"}

    cache.cache_set(cache_key, profile)
    return {"status": "ok", "source": "db", "profile": profile}


def _update_profile(user_id: str, updates: dict) -> dict:
    """Update a user profile."""
    profile = config.get(f"user:{user_id}", {})
    profile.update(updates)
    config.set(f"user:{user_id}", profile)

    # Invalidate cache
    cache.cache_delete(f"profile:{user_id}")

    return {"status": "ok", "profile": profile}


def _compute_score(user_id: str, params: dict) -> dict:
    """Compute a score for a user (expensive, cached)."""
    cache_key = cache.compute_cache_key("score", user_id, params)
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return {"status": "ok", "source": "cache", "score": cached}

    profile = config.get(f"user:{user_id}", None)
    if profile is None:
        return {"status": "error", "message": f"User {user_id} not found"}

    # Simulate an expensive computation
    activity = profile.get("activity_count", 0)
    level = profile.get("level", 1)
    multiplier = params.get("multiplier", 1.0)
    score = round((activity * level * multiplier) / 10.0, 2)

    cache.cache_set(cache_key, score)
    return {"status": "ok", "source": "computed", "score": score}


def handle_admin_request(action: str, payload: dict | None = None) -> dict:
    """Handle an admin request.

    Actions: get_config, set_config, clear_cache, get_stats
    """
    if action == "get_config":
        return {"status": "ok", "config": config.get_all()}
    elif action == "set_config":
        if not payload:
            return {"status": "error", "message": "No payload"}
        for k, v in payload.items():
            config.set(k, v)
        return {"status": "ok"}
    elif action == "clear_cache":
        cache.cache_clear()
        return {"status": "ok", "message": "Cache cleared"}
    elif action == "get_stats":
        return {"status": "ok", "stats": cache.cache_stats()}
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}
