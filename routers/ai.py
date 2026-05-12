"""
routers/ai.py
─────────────
AI endpoints with MCP tool calling, RAG, and response caching.

Fixes applied:
  - C3: Removed unused build_llm_context import
  - C1: cache_hit returned in response (no [cached] prefix)
  - H4: feedback validates response_id exists before saving
  - H5: /history has max limit=100
  - H6: IoT-specific line removed from system prompt template
  - M2: ErrorResponse used in responses={}

✏️ ON HACKATHON DAY: update DOMAIN_NAME and SYSTEM_PROMPT_TEMPLATE only.
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from models.schemas import (
    ChatRequest, ChatResponse,
    FeedbackRequest, FeedbackResponse,
    TranslateRequest, ErrorResponse,
)
from services.LLM import chat, translate
from services.mcp_tools import TOOLS
from services.database import save_chat, save_feedback, response_id_exists
import services.cache as cache
import services.rag as rag

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI"])

# ── ✏️ Change these on hackathon day ──────────────────────────────────────────
DOMAIN_NAME = "IoT Device Management Platform"

SYSTEM_PROMPT_TEMPLATE = """
You are an intelligent AI assistant for {domain}.
You have access to tools to fetch live data, alerts, and system status.
Use tools to answer questions accurately — do not guess or assume values.
Keep answers concise and actionable.
{rag_context}
"""
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={500: {"model": ErrorResponse}},   # M2
)
async def chat_endpoint(req: ChatRequest):
    """
    Main AI chat endpoint.
    - MCP tools: LLM fetches real domain data via tool calls
    - RAG: injects relevant knowledge base chunks into prompt
    - Cache: identical prompts return cached responses (5 min TTL)
    Both RAG and context can be independently toggled per request.
    """
    try:
        # Build RAG context if requested and globally enabled
        rag_context_str = ""
        rag_chunks_count = 0
        rag_actually_used = False

        if req.use_rag and rag.is_enabled():
            rag_context_str, rag_chunks_count = rag.build_rag_context(req.prompt)
            rag_actually_used = rag_chunks_count > 0
            if rag_actually_used:
                logger.debug("RAG injected %d chunks for prompt: %.60s", rag_chunks_count, req.prompt)

        system = SYSTEM_PROMPT_TEMPLATE.format(
            domain=DOMAIN_NAME,
            rag_context=rag_context_str,
        ).strip()

        response, cache_hit = await chat(
            prompt=req.prompt,
            system=system,
            tools=TOOLS if req.include_context else None,
        )

        response_id = await save_chat(req.prompt, response)

        return ChatResponse(
            response=response,
            response_id=response_id,
            context_used=req.include_context,
            cache_hit=cache_hit,             # C1: clean flag instead of prefix
            rag_used=rag_actually_used,
            rag_chunks_count=rag_chunks_count,
        )
    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={404: {"model": ErrorResponse}},   # M2
)
async def feedback_endpoint(req: FeedbackRequest):
    """
    H4: Validates response_id exists before saving.
    H3: rating is Literal[-1, 1] — no neutral 0 accepted.
    Judges explicitly check for this endpoint.
    """
    try:
        if not await response_id_exists(req.response_id):
            raise HTTPException(status_code=404, detail="Response ID not found")
        await save_feedback(req.response_id, req.rating)
        return FeedbackResponse(status="recorded", response_id=req.response_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Feedback endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate")
async def translate_endpoint(req: TranslateRequest):
    try:
        translated = await translate(req.text, req.target_lang)
        return {"original": req.text, "translated": translated, "lang": req.target_lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def cache_stats():
    """Cache statistics — useful during demo to prove optimization."""
    return cache.stats()


@router.delete("/cache")
async def clear_cache():
    """Clear response cache — useful for demo reset."""
    cache.clear()
    return {"status": "cache cleared"}
