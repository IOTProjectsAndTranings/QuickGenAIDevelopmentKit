"""
main.py
───────
FastAPI application entry point.

Fixes applied:
  - M3: Removed unused `import services.cache as cache`
  - M6: Uses Python logging throughout
  - RAG router registered at /api/rag
  - RAG index rebuilt at startup from existing DB docs
"""
import secrets
import logging
import logging.handlers
import os
import time
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import APP_API_KEY, APP_ENV, APP_TITLE
from models.schemas import HealthResponse
from routers import ai, data
from routers import rag as rag_router
from services.LLM import sarvam_health
from services.database import init_db
from services.rate_limiter import RateLimitMiddleware
import services.rag as rag


# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            "logs/app.log", maxBytes=5_000_000, backupCount=3
        ),
    ],
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s ...", APP_TITLE)
    await init_db()
    await rag.rebuild_index()           # Load existing RAG docs into memory
    sarvam_ok = await sarvam_health()
    logger.info("Sarvam AI: %s", "connected" if sarvam_ok else "NOT connected — check SARVAM_API_KEY")
    logger.info("Rate limiting: %s", "active")
    logger.info("RAG: %s", "enabled" if rag.is_enabled() else "disabled")
    logger.info("Swagger docs: http://localhost:8000/docs")
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    description="Hackathon GenAI Starter — Final — MCP · RAG · Cache · Rate Limiting · sarvam-30b",
    version="4.0.0",
    lifespan=lifespan,
)

# ── Middleware (rate limit before CORS) ───────────────────────────────────────
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API key security ──────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_key(key: str = Security(api_key_header)):
    if key != APP_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(ai.router,         prefix="/api/ai",   dependencies=[Depends(verify_key)])
app.include_router(data.router,       prefix="/api/data", dependencies=[Depends(verify_key)])
app.include_router(rag_router.router, prefix="/api/rag",  dependencies=[Depends(verify_key)])

# ── Static frontend ───────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    sarvam_ok = await sarvam_health()
    return HealthResponse(status="ok", sarvam_connected=sarvam_ok, env=APP_ENV)


# In-memory token store: token → expiry timestamp
_session_tokens: dict[str, float] = {}

@app.get("/api/session", include_in_schema=False)
async def get_session_token():
    """
    Issues a short-lived session token to the browser.
    The real APP_API_KEY is never exposed to the frontend.
    Token expires in 8 hours — covers a full hackathon day.
    """
    token = secrets.token_urlsafe(32)
    _session_tokens[token] = time.time() + (8 * 3600)   # 8 hour expiry
    return {"token": token}

# Update verify_key to accept session tokens too
async def verify_key(key: str = Security(api_key_header)):
    # Accept real APP_API_KEY (for REST client / API testing)
    if key == APP_API_KEY:
        return key
    # Accept valid session tokens (for browser)
    expiry = _session_tokens.get(key)
    if expiry and time.time() < expiry:
        return key
    raise HTTPException(status_code=403, detail="Invalid or expired key")