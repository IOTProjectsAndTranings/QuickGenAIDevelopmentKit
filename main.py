"""
main.py
───────
FastAPI application entry point.
Run with: uvicorn main:app --reload
Or press F5 in VS Code.
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


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    await init_db()
    sarvam_ok = await sarvam_health()
    print(f"✅ DB initialized")
    print(f"{'✅' if sarvam_ok else '❌'} Sarvam AI: {'connected' if sarvam_ok else 'NOT connected — check API key'}")
    yield
    print("🔴 Shutting down...")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    description="Hackathon GenAI Starter — swap mock_data.py per problem",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to localhost in prod
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

# ── Frontend static serving ───────────────────────────────────────────────────
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
        env=APP_ENV
    )
