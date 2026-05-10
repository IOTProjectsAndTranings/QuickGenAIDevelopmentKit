"""
services/sarvam.py
─────────────────
Wrapper around Sarvam AI APIs.
Compatible with latest Sarvam API format.
"""

import httpx
from config import SARVAM_API_KEY, SARVAM_BASE_URL, SARVAM_MODEL

HEADERS = {
    "Authorization": f"Bearer {SARVAM_API_KEY}",
    "Content-Type": "application/json",
}


# ── LLM Chat ─────────────────────────────────────────────────────────────────
async def chat(
    prompt: str,
    system: str = "You are a helpful assistant.",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Core LLM call using latest Sarvam Chat Completions API.
    """

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
        response = await client.post(
            f"{SARVAM_BASE_URL}/v1/chat/completions",
            headers=HEADERS,
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]


# ── Translation ───────────────────────────────────────────────────────────────
async def translate(
    text: str,
    target_lang: str = "hi-IN",
    source_lang: str = "auto",
) -> str:
    """
    Translate text to target language.
    """

    payload = {
        "input": text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{SARVAM_BASE_URL}/translate",
            headers=HEADERS,
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

        return data.get("translated_text", text)


# ── Text to Speech ────────────────────────────────────────────────────────────
async def text_to_speech(
    text: str,
    lang: str = "en-IN",
    speaker: str = "meera",
) -> bytes:
    """
    Convert text to speech.
    Returns raw audio bytes.
    """

    payload = {
        "inputs": [text],
        "target_language_code": lang,
        "speaker": speaker,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{SARVAM_BASE_URL}/text-to-speech",
            headers=HEADERS,
            json=payload,
        )

        response.raise_for_status()

        return response.content


# ── Health Check ──────────────────────────────────────────────────────────────
async def sarvam_health() -> bool:
    """
    Verify Sarvam API connectivity.
    """

    try:
        result = await chat(
            prompt="ping",
            system="Reply only with pong",
            temperature=0,
            max_tokens=1000,
        )

        return "pong" in result.lower()

    except Exception as e:
        print(f"Sarvam health check failed: {e}")
        return False
