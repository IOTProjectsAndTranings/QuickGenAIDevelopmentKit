"""
services/cache.py
─────────────────
Simple in-memory TTL cache for LLM responses.
Prevents repeat Sarvam API calls for identical prompts.
Saves API credits during demo — same question asked twice won't hit Sarvam again.

On hackathon day: no changes needed.
"""

import hashlib
import time
from config import CACHE_TTL_SECONDS

_store: dict[str, tuple[str, float]] = {}   # key → (value, timestamp)


def _make_key(prompt: str, system: str) -> str:
    raw = f"{system.strip()[:100]}|{prompt.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


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
    return {"total_keys": len(_store), "active_keys": active, "ttl_seconds": CACHE_TTL_SECONDS}


def clear() -> None:
    _store.clear()
