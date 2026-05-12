"""
services/cache.py
─────────────────
In-memory TTL cache for LLM responses.

Fixes applied:
  - L2: SHA-256 instead of MD5 for cache keys
"""

import hashlib
import logging
import time
from config import CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)
_store: dict[str, tuple[str, float]] = {}   # key → (value, timestamp)


def _make_key(prompt: str, system: str) -> str:
    raw = f"{system.strip()[:100]}|{prompt.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()   # L2: SHA-256


def get(prompt: str, system: str) -> str | None:
    key = _make_key(prompt, system)
    if key in _store:
        value, ts = _store[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return value
        del _store[key]
    return None


def set(prompt: str, system: str, response: str) -> None:
    key = _make_key(prompt, system)
    _store[key] = (response, time.time())


def stats() -> dict:
    now = time.time()
    active = sum(1 for _, ts in _store.values() if now - ts < CACHE_TTL_SECONDS)
    return {
        "total_keys": len(_store),
        "active_keys": active,
        "ttl_seconds": CACHE_TTL_SECONDS,
    }


def clear() -> None:
    count = len(_store)
    _store.clear()
    logger.info("Cache cleared (%d entries removed)", count)
