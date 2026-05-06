"""
models/schemas.py
─────────────────
All request/response Pydantic models.
Add new models here as your problem domain requires.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, List


# ── AI Endpoints ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, example="Show me all offline devices")
    include_context: bool = Field(True, description="Auto-inject domain data as LLM context")


class ChatResponse(BaseModel):
    response: str
    response_id: str
    context_used: bool


class FeedbackRequest(BaseModel):
    response_id: str
    rating: int = Field(..., ge=-1, le=1, description="1 = thumbs up, -1 = thumbs down")


class FeedbackResponse(BaseModel):
    status: str
    response_id: str


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = Field("hi-IN", example="hi-IN")


# ── Data Endpoints ────────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    id: str
    name: str
    status: str
    value: Optional[Any] = None


class AlertResponse(BaseModel):
    id: str
    device_id: str
    severity: str
    message: str


# ── Generic ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    sarvam_connected: bool
    env: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
