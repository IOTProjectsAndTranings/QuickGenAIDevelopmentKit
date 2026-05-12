"""
models/schemas.py
─────────────────
Pydantic request/response models.

Fixes applied:
  - H3: FeedbackRequest.rating uses Literal[-1, 1] — no rating=0
  - C1: ChatResponse has cache_hit field
  - RAG schemas added
  - M2: ErrorResponse now used in router response_model
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ── AI ────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, example="Show me all offline devices")
    include_context: bool = Field(True,  description="Inject MCP tool data as LLM context")
    use_rag: bool         = Field(False, description="Include RAG knowledge base context")


class ChatResponse(BaseModel):
    response: str
    response_id: str
    context_used: bool
    cache_hit: bool       = False   # C1: was hidden by [cached] prefix before
    rag_used: bool        = False
    rag_chunks_count: int = 0


class FeedbackRequest(BaseModel):
    response_id: str
    rating: Literal[-1, 1] = Field(..., description="1 = thumbs up, -1 = thumbs down")  # H3


class FeedbackResponse(BaseModel):
    status: str
    response_id: str


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = Field("hi-IN", example="hi-IN")


# ── RAG ───────────────────────────────────────────────────────────────────────

class RagUploadRequest(BaseModel):
    name: str    = Field(..., min_length=1, max_length=200, description="Document name/title")
    content: str = Field(..., min_length=10, description="Plain text content to index")


class RagDocumentResponse(BaseModel):
    id: str
    name: str
    chunk_count: int
    created_at: float


class RagToggleResponse(BaseModel):
    enabled: bool
    message: str


class RagStatusResponse(BaseModel):
    enabled: bool
    doc_count: int
    indexed_chunks: int


# ── Data ──────────────────────────────────────────────────────────────────────

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


# ── System ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    sarvam_connected: bool
    env: str


class ErrorResponse(BaseModel):   # M2: now actually used in routers
    error: str
    detail: Optional[str] = None
