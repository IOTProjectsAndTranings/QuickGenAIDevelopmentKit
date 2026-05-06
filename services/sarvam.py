"""
services/sarvam.py
─────────────────
Wrapper around Sarvam AI APIs.
On hackathon day: only change the system prompt — nothing else.
"""

import httpx
from config import SARVAM_API_KEY, SARVAM_BASE_URL, SARVAM_MODEL

HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json",
}

# ── LLM Chat ─────────────────────────────────────────────────────────────────
async def chat(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """
    Core LLM call. Inject domain context via `system` param.
    Change system prompt per problem — everything else stays same.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": SARVAM_MODEL,
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
    """Translate text to target language. Useful for multilingual problem statements."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/translate",
            headers=HEADERS,
            json={"input": text, "target_language_code": target_lang},
        )
        resp.raise_for_status()
        return resp.json().get("translated_text", text)


# ── Text to Speech ────────────────────────────────────────────────────────────
async def text_to_speech(text: str, lang: str = "en-IN") -> bytes:
    """Returns audio bytes. Useful if problem needs voice output."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/text-to-speech",
            headers=HEADERS,
            json={"input": text, "target_language_code": lang},
        )
        resp.raise_for_status()
        return resp.content


# ── Health Check ──────────────────────────────────────────────────────────────
async def sarvam_health() -> bool:
    """Ping Sarvam to verify API key works. Call at startup."""
    try:
        result = await chat("ping", "Reply with: pong")
        return bool(result)
    except Exception:
        return False
