"""
services/sarvam.py
──────────────────
Sarvam AI wrapper with:
  - MCP-style tool calling
  - Automatic fallback handling
  - Graceful API error handling
  - Response caching

Compatible with latest Sarvam API.
"""

import json
import httpx

from config import (
    SARVAM_API_KEY,
    SARVAM_BASE_URL,
    SARVAM_MODEL,
)

import services.cache as cache


# ── Headers ──────────────────────────────────────────────────────────────────
HEADERS = {
    "Authorization": f"Bearer {SARVAM_API_KEY}",
    "Content-Type": "application/json",
}


# ── Offline fallback ─────────────────────────────────────────────────────────
_FALLBACK = (
    "I'm currently unable to connect to the AI backend. "
    "Based on system data: {context}"
)


# ── Helper: Safe Content Extraction ──────────────────────────────────────────
def _extract_content(data: dict) -> str:
    """
    Safely extract assistant message content from Sarvam response.
    """

    try:
        choices = data.get("choices", [])

        if not choices:
            return ""

        message = choices[0].get("message", {})

        content = message.get("content")

        if content is None:
            return ""

        return str(content)

    except Exception:
        return ""


# ── Core Chat ────────────────────────────────────────────────────────────────
async def chat(
    prompt: str,
    system: str = "You are a helpful assistant.",
    tools: list | None = None,
    temperature: float = 0.7,
    max_tokens: int = 5000,
) -> str:
    """
    Main LLM call.
    """

    # Cache lookup
    cached = cache.get(prompt, system)

    if cached:
        return f"[cached] {cached}"

    try:
        if tools:
            response = await _chat_with_tools(
                prompt=prompt,
                system=system,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            response = await _chat_plain(
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        cache.set(prompt, system, response)

        return response

    except httpx.TimeoutException:
        return _FALLBACK.format(
            context="Request timed out — Sarvam API too slow."
        )

    except httpx.HTTPStatusError as e:

        if e.response.status_code == 401:
            return "Authentication failed — invalid SARVAM_API_KEY"

        if e.response.status_code == 429:
            return "Sarvam rate limit hit — please retry shortly."

        return (
            f"Sarvam API error ({e.response.status_code}) — "
            f"{e.response.text[:200]}"
        )

    except Exception as e:
        return _FALLBACK.format(
            context=f"Unexpected error: {str(e)[:100]}"
        )


# ── Tool Calling ─────────────────────────────────────────────────────────────
async def _chat_with_tools(
    prompt: str,
    system: str,
    tools: list,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    OpenAI-compatible MCP tool calling.
    """

    from services.mcp_tools import execute_tool

    messages = [
        {
            "role": "system",
            "content": system,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    async with httpx.AsyncClient(timeout=30) as client:

        payload = {
            "model": SARVAM_MODEL,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = await client.post(
            f"{SARVAM_BASE_URL}/chat/completions",
            headers=HEADERS,
            json=payload,
        )

        resp.raise_for_status()

        data = resp.json()

        choice = data.get("choices", [{}])[0]

        message = choice.get("message", {})

        tool_calls = message.get("tool_calls")

        # ── Tool execution loop ─────────────────────────────────────────────
        if tool_calls:

            messages.append(message)

            for tc in tool_calls:

                fn_name = tc["function"]["name"]

                fn_args = json.loads(
                    tc["function"].get("arguments", "{}")
                )

                result = execute_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result),
                })

            # ── Follow-up completion ───────────────────────────────────────
            followup_payload = {
                "model": SARVAM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            resp2 = await client.post(
                f"{SARVAM_BASE_URL}/chat/completions",
                headers=HEADERS,
                json=followup_payload,
            )

            resp2.raise_for_status()

            data2 = resp2.json()

            return _extract_content(data2)

        # ── Normal text response ───────────────────────────────────────────
        return _extract_content(data)


# ── Plain Chat ───────────────────────────────────────────────────────────────
async def _chat_plain(
    prompt: str,
    system: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:

    payload = {
        "model": SARVAM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=30) as client:

        resp = await client.post(
            f"{SARVAM_BASE_URL}/chat/completions",
            headers=HEADERS,
            json=payload,
        )

        resp.raise_for_status()

        data = resp.json()

        return _extract_content(data)


# ── Translation ──────────────────────────────────────────────────────────────
async def translate(
    text: str,
    target_lang: str = "hi-IN",
    source_lang: str = "auto",
) -> str:

    payload = {
        "input": text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
    }

    async with httpx.AsyncClient(timeout=15) as client:

        resp = await client.post(
            f"{SARVAM_BASE_URL}/translate",
            headers=HEADERS,
            json=payload,
        )

        resp.raise_for_status()

        data = resp.json()

        return data.get("translated_text", text)


# ── Health Check ─────────────────────────────────────────────────────────────
async def sarvam_health() -> bool:
    """
    Verify Sarvam API connectivity.
    """

    try:

        result = await _chat_plain(
            prompt="ping",
            system="Reply only with pong",
            temperature=0,
            max_tokens=1000,
        )

        if not result:
            return False

        return "pong" in result.lower()

    except Exception as e:
        print(f"Sarvam health check failed: {e}")
        return False