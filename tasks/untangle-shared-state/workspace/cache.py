"""Caching module that uses config for storage.

Uses the config module to store cache entries under a "cache:" prefix.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import config


def _cache_key(key: str) -> str:
    """Generate a config key for a cache entry."""
    return f"cache:{key}"


def _meta_key(key: str) -> str:
    """Generate a config key for cache metadata (TTL tracking)."""
    return f"cache_meta:{key}"


def cache_get(key: str) -> Any | None:
    """Get a cached value. Returns None if not found or expired."""
    if not config.get("cache_enabled", True):
        return None

    meta = config.get(_meta_key(key))
    if meta is not None:
        ttl = config.get("cache_ttl_sec", 300)
        if time.time() - meta["stored_at"] > ttl:
            # Expired — remove it
            cache_delete(key)
            return None

    return config.get(_cache_key(key))


def cache_set(key: str, value: Any) -> None:
    """Store a value in the cache."""
    if not config.get("cache_enabled", True):
        return

    config.set(_cache_key(key), value)
    config.set(_meta_key(key), {"stored_at": time.time()})


def cache_delete(key: str) -> None:
    """Remove a value from the cache."""
    # We can't truly delete from config, so set to None
    config.set(_cache_key(key), None)
    config.set(_meta_key(key), None)


def cache_clear() -> None:
    """Clear all cache entries from config."""
    all_config = config.get_all()
    for k in list(all_config.keys()):
        if k.startswith("cache:") or k.startswith("cache_meta:"):
            config.set(k, None)


def cache_stats() -> dict[str, int]:
    """Return cache statistics."""
    all_config = config.get_all()
    total = 0
    active = 0
    for k, v in all_config.items():
        if k.startswith("cache:") and v is not None:
            total += 1
            meta = all_config.get(k.replace("cache:", "cache_meta:"))
            if meta is not None:
                ttl = config.get("cache_ttl_sec", 300)
                if time.time() - meta["stored_at"] <= ttl:
                    active += 1
    return {"total": total, "active": active}


def compute_cache_key(*args: Any) -> str:
    """Compute a deterministic cache key from arguments."""
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
