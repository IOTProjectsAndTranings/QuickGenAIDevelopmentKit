"""
routers/data.py
───────────────
Domain data endpoints.
These serve mock data that the frontend displays directly (not via LLM).
✏️ Rename 'entities' to your domain (employees, products, devices, etc.)
"""

from fastapi import APIRouter, HTTPException
from services.mock_data import get_all_entities, get_entity_by_id, get_entities_by_status, get_alerts
from services.database import get_chat_history

router = APIRouter(tags=["Data"])


@router.get("/entities")
async def list_entities():
    """Return all domain entities (devices / employees / products)."""
    return {"data": get_all_entities(), "count": len(get_all_entities())}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities/status/{status}")
async def filter_by_status(status: str):
    """Filter entities by status: online / offline / warning."""
    results = get_entities_by_status(status)
    return {"data": results, "count": len(results)}


@router.get("/alerts")
async def list_alerts():
    """Return all active alerts."""
    return {"data": get_alerts(), "count": len(get_alerts())}


@router.get("/history")
async def chat_history(limit: int = 20):
    """Return recent chat history from DB."""
    history = await get_chat_history(limit)
    return {"data": history, "count": len(history)}
