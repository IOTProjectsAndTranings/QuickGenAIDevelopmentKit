"""
routers/ai.py
─────────────
AI endpoints — now with MCP tool calling and response caching.

✏️ ON HACKATHON DAY:
  - Update DOMAIN_NAME
  - Update SYSTEM_PROMPT_TEMPLATE context description
  - That's it — tools, cache, fallback all work automatically
"""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    ChatRequest, ChatResponse,
    FeedbackRequest, FeedbackResponse,
    TranslateRequest,
)
from services.sarvam import chat, translate
from services.mock_data import build_llm_context
from services.mcp_tools import TOOLS
from services.database import save_chat, save_feedback
import services.cache as cache

router = APIRouter(tags=["AI"])

# ✏️ Change these two on hackathon day ─────────────────────────────────────────
DOMAIN_NAME = "IoT Device Management Platform"

SYSTEM_PROMPT_TEMPLATE = """
You are an intelligent AI assistant for {domain}.
You have access to tools to fetch live device data, alerts, and system status.
Use tools to answer questions accurately — do not guess or assume device values.
Keep answers concise and actionable.
If a device is offline, suggest common troubleshooting steps relevant to its protocol.
"""
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main AI chat — uses MCP tool calling so LLM fetches real data.
    Falls back to context injection if tools not supported.
    Responses are cached for 5 min.
    """
    try:
        system = SYSTEM_PROMPT_TEMPLATE.format(domain=DOMAIN_NAME)

        if req.include_context:
            # MCP tool calling path
            response = await chat(req.prompt, system, tools=TOOLS)
        else:
            # Plain LLM — no domain data
            response = await chat(req.prompt, system, tools=None)

        response_id = await save_chat(req.prompt, response)

        return ChatResponse(
            response=response,
            response_id=response_id,
            context_used=req.include_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(req: FeedbackRequest):
    """
    Thumbs up / thumbs down on AI responses.
    Explicitly required by hackathon judging criteria.
    rating: 1 = thumbs up, -1 = thumbs down
    """
    try:
        await save_feedback(req.response_id, req.rating)
        return FeedbackResponse(status="recorded", response_id=req.response_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate")
async def translate_endpoint(req: TranslateRequest):
    """Translate text using Sarvam translation API."""
    try:
        translated = await translate(req.text, req.target_lang)
        return {"original": req.text, "translated": translated, "lang": req.target_lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def cache_stats():
    """Show cache statistics — useful during demo to prove optimization."""
    return cache.stats()


@router.delete("/cache")
async def clear_cache():
    """Clear response cache — useful during demo reset."""
    cache.clear()
    return {"status": "cache cleared"}
