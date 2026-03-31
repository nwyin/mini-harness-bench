"""Caching module that uses a config instance for storage.

Uses a Config instance to store cache entries under a "cache:" prefix.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from config import Config


def _cache_key(key: str) -> str:
    """Generate a config key for a cache entry."""
    return f"cache:{key}"


def _meta_key(key: str) -> str:
    """Generate a config key for cache metadata (TTL tracking)."""
    return f"cache_meta:{key}"


class Cache:
    """Cache backed by a Config instance."""

    def __init__(self, cfg: Config):
        self._cfg = cfg

    def cache_get(self, key: str) -> Any | None:
        """Get a cached value. Returns None if not found or expired."""
        if not self._cfg.get("cache_enabled", True):
            return None

        meta = self._cfg.get(_meta_key(key))
        if meta is not None:
            ttl = self._cfg.get("cache_ttl_sec", 300)
            if time.time() - meta["stored_at"] > ttl:
                self.cache_delete(key)
                return None

        return self._cfg.get(_cache_key(key))

    def cache_set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        if not self._cfg.get("cache_enabled", True):
            return

        self._cfg.set(_cache_key(key), value)
        self._cfg.set(_meta_key(key), {"stored_at": time.time()})

    def cache_delete(self, key: str) -> None:
        """Remove a value from the cache."""
        self._cfg.set(_cache_key(key), None)
        self._cfg.set(_meta_key(key), None)

    def cache_clear(self) -> None:
        """Clear all cache entries from config."""
        all_config = self._cfg.get_all()
        for k in list(all_config.keys()):
            if k.startswith("cache:") or k.startswith("cache_meta:"):
                self._cfg.set(k, None)

    def cache_stats(self) -> dict[str, int]:
        """Return cache statistics."""
        all_config = self._cfg.get_all()
        total = 0
        active = 0
        for k, v in all_config.items():
            if k.startswith("cache:") and v is not None:
                total += 1
                meta = all_config.get(k.replace("cache:", "cache_meta:"))
                if meta is not None:
                    ttl = self._cfg.get("cache_ttl_sec", 300)
                    if time.time() - meta["stored_at"] <= ttl:
                        active += 1
        return {"total": total, "active": active}


# Module-level convenience functions for backward compatibility
import config as _config_module  # noqa: E402

_default_cache = Cache(_config_module._default)


def cache_get(key: str) -> Any | None:
    return _default_cache.cache_get(key)


def cache_set(key: str, value: Any) -> None:
    _default_cache.cache_set(key, value)


def cache_delete(key: str) -> None:
    _default_cache.cache_delete(key)


def cache_clear() -> None:
    _default_cache.cache_clear()


def cache_stats() -> dict[str, int]:
    return _default_cache.cache_stats()


def compute_cache_key(*args: Any) -> str:
    """Compute a deterministic cache key from arguments."""
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
