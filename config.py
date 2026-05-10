from dotenv import load_dotenv
import os

load_dotenv()

SARVAM_API_KEY  = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"
SARVAM_MODEL    = "sarvam-2b"

APP_API_KEY = os.getenv("APP_API_KEY", "hackathon-secret-key-123")
APP_ENV     = os.getenv("APP_ENV", "development")
APP_TITLE   = os.getenv("APP_TITLE", "Hackathon AI App")

DB_PATH = "db/hackathon.db"

# Rate limiting
RATE_LIMIT_REQUESTS = 30       # per window
RATE_LIMIT_WINDOW   = 60       # seconds

# Cache
CACHE_TTL_SECONDS = 300        # 5 minutes
