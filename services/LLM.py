"""
services/LLM.py
───────────────
Generic LLM wrapper — currently backed by Sarvam AI.
Renamed from sarvam.py to LLM.py to stay provider-agnostic.
Swap the internals here if you switch to a different LLM on hackathon day.

Features:
  - MCP tool calling with up to MAX_TOOL_ROUNDS rounds
  - 60s cached health check (no credit burn on /health polls)
  - Response cache (TTL-based, SHA-256 keyed)
  - Graceful fallback on timeout / API errors
  - Full structured logging
"""

import json
import logging
import time
import httpx

from config import SARVAM_API_KEY, SARVAM_BASE_URL, SARVAM_MODEL
import services.cache as cache

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3   # max chained tool call rounds before forcing final response

# ── Headers (lazy — key is validated at startup) ──────────────────────────────
def _get_headers() -> dict:
    return {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

_FALLBACK = "I'm temporarily unable to reach the AI backend. Please try again. (Reason: {reason})"

# ── Health cache (H1 fix) ─────────────────────────────────────────────────────
_health_cache: tuple[bool, float] | None = None


# ── Public chat interface ─────────────────────────────────────────────────────

async def chat(
    prompt: str,
    system: str = "You are a helpful assistant.",
    tools: list | None = None,
) -> tuple[str, bool]:
    """
    Main LLM call. Returns (response_text, cache_hit).
    Checks cache → calls Sarvam → stores in cache.
    Uses MCP tool calling if tools provided.
    """
    cached = cache.get(prompt, system)
    if cached is not None:
        logger.debug("Cache hit: %.60s", prompt)
        return cached, True

    try:
        if tools:
            response = await _chat_with_tools(prompt, system, tools)
        else:
            response = await _chat_plain(prompt, system)

        cache.set(prompt, system, response)
        return response, False

    except httpx.TimeoutException:
        logger.warning("LLM API timeout")
        return _FALLBACK.format(reason="timeout"), False
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 401:
            logger.error("LLM 401 — check SARVAM_API_KEY")
            return "Authentication failed — check SARVAM_API_KEY in .env", False
        if code == 429:
            logger.warning("LLM rate limit hit")
            return "LLM rate limit hit — please wait a moment.", False
        logger.error("LLM HTTP %d: %s", code, e.response.text[:200])
        return _FALLBACK.format(reason=f"HTTP {code}"), False
    except Exception as e:
        logger.exception("Unexpected LLM error")
        return _FALLBACK.format(reason=str(e)[:80]), False


# ── MCP tool calling loop ─────────────────────────────────────────────────────

async def _chat_with_tools(prompt: str, system: str, tools: list) -> str:
    from services.mcp_tools import execute_tool

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            for round_num in range(MAX_TOOL_ROUNDS):
                resp = await client.post(
                    f"{SARVAM_BASE_URL}/chat/completions",
                    headers=_get_headers(),
                    json={
                        "model":       SARVAM_MODEL,
                        "messages":    messages,
                        "tools":       tools,
                        "tool_choice": "auto",
                    },
                )
                resp.raise_for_status()
                choice     = resp.json()["choices"][0]
                tool_calls = choice["message"].get("tool_calls")

                if not tool_calls:
                    return choice["message"]["content"]

                messages.append(choice["message"])
                logger.debug("Tool round %d: %d call(s)", round_num + 1, len(tool_calls))

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"].get("arguments", "{}"))
                    result  = execute_tool(fn_name, fn_args)
                    messages.append({
                        "role":         "tool",
                        "tool_call_id": tc["id"],
                        "content":      json.dumps(result),
                    })

            # Max rounds reached — one final plain call
            logger.warning("MAX_TOOL_ROUNDS (%d) reached — forcing final response", MAX_TOOL_ROUNDS)
            resp = await client.post(
                f"{SARVAM_BASE_URL}/chat/completions",
                headers=_get_headers(),
                json={"model": SARVAM_MODEL, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        except (KeyError, json.JSONDecodeError):
            logger.info("Tool calling not supported — falling back to plain chat")
            return await _chat_plain(prompt, system)


# ── Plain chat ────────────────────────────────────────────────────────────────

async def _chat_plain(prompt: str, system: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/chat/completions",
            headers=_get_headers(),
            json={
                "model":    SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── Translation ───────────────────────────────────────────────────────────────

async def translate(text: str, target_lang: str = "hi-IN") -> str:
    """Sarvam translate — note: uses base URL without /v1 for this endpoint."""
    base = SARVAM_BASE_URL.rstrip("/v1").rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{base}/translate",
            headers=_get_headers(),
            json={"input": text, "target_language_code": target_lang},
        )
        resp.raise_for_status()
        return resp.json().get("translated_text", text)


# ── Health (cached 60s) ───────────────────────────────────────────────────────

async def sarvam_health() -> bool:
    global _health_cache
    now = time.time()
    if _health_cache and (now - _health_cache[1]) < 60:
        return _health_cache[0]
    try:
        await _chat_plain("ping", "Reply with exactly one word: pong")
        _health_cache = (True, now)
        return True
    except Exception:
        _health_cache = (False, now)
        return False
