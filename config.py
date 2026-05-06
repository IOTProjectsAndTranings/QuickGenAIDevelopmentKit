from dotenv import load_dotenv
import os

load_dotenv()

# ── Sarvam AI ────────────────────────────────────────────
SARVAM_API_KEY  = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"
SARVAM_MODEL    = "sarvam-2b"          # Change if hackathon provides different model

# ── App ──────────────────────────────────────────────────
APP_API_KEY = os.getenv("APP_API_KEY", "hackathon-secret-key-123")
APP_ENV     = os.getenv("APP_ENV", "development")
APP_TITLE   = os.getenv("APP_TITLE", "Hackathon AI App")

# ── DB ───────────────────────────────────────────────────
DB_PATH = "db/hackathon.db"
