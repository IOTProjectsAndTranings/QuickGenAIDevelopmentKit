"""
main.py
───────
FastAPI application with:
  - Rate limiting middleware
  - API key authentication
  - CORS
  - Static frontend serving
  - Startup health checks
"""

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from config import APP_API_KEY, APP_ENV, APP_TITLE
from models.schemas import HealthResponse
from routers import ai, data
from services.sarvam import sarvam_health
from services.database import init_db
from services.rate_limiter import RateLimitMiddleware
import services.cache as cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Hackathon AI App...")
    await init_db()
    sarvam_ok = await sarvam_health()
    print("✅ Database initialized")
    print(f"{'✅' if sarvam_ok else '❌'} Sarvam AI: {'connected' if sarvam_ok else 'NOT connected — check SARVAM_API_KEY'}")
    print(f"✅ Rate limiting: 30 req/min per IP")
    print(f"✅ Response cache: 5 min TTL")
    print(f"✅ MCP tools: {5} tools registered")
    print(f"📖 Swagger: http://localhost:8000/docs")
    yield
    print("🔴 Shutting down...")


app = FastAPI(
    title=APP_TITLE,
    description="Hackathon GenAI Starter — MCP tools, cache, rate limiting, fallback",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Middleware (order matters — rate limit before CORS) ───────────────────────
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Key Security ──────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_key(key: str = Security(api_key_header)):
    if key != APP_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(ai.router,   prefix="/api/ai",   dependencies=[Depends(verify_key)])
app.include_router(data.router, prefix="/api/data", dependencies=[Depends(verify_key)])

# ── Frontend ──────────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    sarvam_ok = await sarvam_health()
    return HealthResponse(
        status="ok",
        sarvam_connected=sarvam_ok,
        env=APP_ENV,
    )
