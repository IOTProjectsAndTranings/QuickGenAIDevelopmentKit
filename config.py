"""
config.py
─────────
Central configuration loaded from .env.
Raises clear errors at startup if required keys are missing.

Repo changes applied:
  - SARVAM_BASE_URL updated to https://api.sarvam.ai/v1  (correct endpoint)
  - SARVAM_MODEL updated to sarvam-30b                   (upgraded model)
"""

from dotenv import load_dotenv
import os

load_dotenv()

# ── LLM (Sarvam AI) ───────────────────────────────────────────────────────────
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    raise ValueError(
        "SARVAM_API_KEY is not set in .env\n"
        "Copy .env.example to .env and add your Sarvam API key."
    )

SARVAM_BASE_URL = "https://api.sarvam.ai/v1"   # ← your fix: correct v1 endpoint
SARVAM_MODEL    = "sarvam-30b"                  # ← your fix: upgraded model

# ── App ───────────────────────────────────────────────────────────────────────
APP_API_KEY = os.getenv("APP_API_KEY")
if not APP_API_KEY:
    raise ValueError(
        "APP_API_KEY is not set in .env\n"
        "Set APP_API_KEY=your-secret-key in .env"
    )

APP_ENV   = os.getenv("APP_ENV",   "development")
APP_TITLE = os.getenv("APP_TITLE", "Hackathon AI App")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = "db/hackathon.db"

# ── Rate limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW   = int(os.getenv("RATE_LIMIT_WINDOW",   "60"))

# ── Response cache ────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# ── RAG ───────────────────────────────────────────────────────────────────────
RAG_CHUNK_SIZE      = int(os.getenv("RAG_CHUNK_SIZE",    "500"))
RAG_CHUNK_OVERLAP   = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
RAG_TOP_K           = int(os.getenv("RAG_TOP_K",         "3"))
RAG_ENABLED_DEFAULT = os.getenv("RAG_ENABLED", "true").lower() == "true"
