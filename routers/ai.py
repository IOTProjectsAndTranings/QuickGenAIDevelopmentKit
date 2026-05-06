"""
routers/ai.py
─────────────
All AI-powered endpoints.
/chat   — main LLM interaction
/feedback — judges look for this explicitly
/translate — bonus multilingual support
"""

from fastapi import APIRouter, HTTPException
from models.schemas import (
    ChatRequest, ChatResponse,
    FeedbackRequest, FeedbackResponse,
    TranslateRequest,
)
from services.sarvam import chat, translate
from services.mock_data import build_llm_context
from services.database import save_chat, save_feedback

router = APIRouter(tags=["AI"])

# ── System Prompt ─────────────────────────────────────────────────────────────
# ✏️ UPDATE THIS on hackathon day to match your problem domain
SYSTEM_PROMPT_TEMPLATE = """
You are an intelligent assistant for {domain}.
Answer questions clearly and concisely.
When referring to entities, use their exact names and IDs.
If you don't know something, say so — do not guess.

Current system data:
{context}
"""


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Main AI chat endpoint. Auto-injects live domain context into LLM."""
    try:
        context = build_llm_context() if req.include_context else ""
        system  = SYSTEM_PROMPT_TEMPLATE.format(
            domain="IoT Device Management",   # ✏️ Change on hackathon day
            context=context
        )
        response    = await chat(req.prompt, system)
        response_id = await save_chat(req.prompt, response)
        return ChatResponse(
            response=response,
            response_id=response_id,
            context_used=req.include_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(req: FeedbackRequest):
    """
    Feedback collection — explicitly listed in judging criteria.
    rating: 1 = thumbs up, -1 = thumbs down
    """
    try:
        await save_feedback(req.response_id, req.rating)
        return FeedbackResponse(status="recorded", response_id=req.response_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate")
async def translate_endpoint(req: TranslateRequest):
    """Translate text to target language using Sarvam."""
    try:
        translated = await translate(req.text, req.target_lang)
        return {"original": req.text, "translated": translated, "lang": req.target_lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
