"""
routers/data.py
───────────────
Domain data endpoints.

Fixes applied:
  - C2: /entities/by-status/{status} defined before /entities/{entity_id}
  - H2: get_all_entities() and get_alerts() called only once per endpoint
  - H5: /history has Query(le=100) max limit
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from models.schemas import ErrorResponse
from services.mock_data import get_all_entities, get_entity_by_id, get_entities_by_status, get_alerts
from services.database import get_chat_history

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data"])


# C2: specific routes first — before parameterized /entities/{entity_id}
@router.get("/entities/by-status/{status}")
async def filter_by_status(status: str):
    """Filter entities by status: online / offline / warning."""
    results = get_entities_by_status(status)   # H2: called once
    return {"data": results, "count": len(results)}


@router.get("/entities/{entity_id}", responses={404: {"model": ErrorResponse}})
async def get_entity(entity_id: str):
    entity = get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/entities")
async def list_entities():
    entities = get_all_entities()   # H2: called once
    return {"data": entities, "count": len(entities)}


@router.get("/alerts")
async def list_alerts():
    alerts = get_alerts()           # H2: called once
    return {"data": alerts, "count": len(alerts)}


@router.get("/history")
async def chat_history(
    limit: int = Query(default=20, ge=1, le=100)   # H5: max 100
):
    """Return recent chat history from DB."""
    history = await get_chat_history(limit)
    return {"data": history, "count": len(history)}
