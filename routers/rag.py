"""
routers/rag.py
──────────────
RAG management endpoints.

POST   /api/rag/upload              — upload a text document for indexing
GET    /api/rag/documents           — list all indexed documents
DELETE /api/rag/documents/{doc_id} — delete a document and its chunks
GET    /api/rag/status              — global RAG status + stats
POST   /api/rag/toggle              — enable / disable RAG globally
"""

import logging
from fastapi import APIRouter, HTTPException

from models.schemas import (
    RagUploadRequest, RagDocumentResponse,
    RagToggleResponse, RagStatusResponse, ErrorResponse,
)
from services.database import save_rag_document, delete_rag_document_db, get_rag_documents
import services.rag as rag

logger = logging.getLogger(__name__)
router = APIRouter(tags=["RAG"])


@router.get("/status", response_model=RagStatusResponse)
async def rag_status():
    """Current RAG state — enabled/disabled, doc count, index size."""
    docs = await get_rag_documents()
    stats = rag.index_stats()
    return RagStatusResponse(
        enabled=stats["enabled"],
        doc_count=len(docs),
        indexed_chunks=stats["indexed_chunks"],
    )


@router.post("/toggle", response_model=RagToggleResponse)
async def toggle_rag():
    """Flip the global RAG toggle. Affects all subsequent requests."""
    new_state = rag.toggle()
    return RagToggleResponse(
        enabled=new_state,
        message=f"RAG {'enabled' if new_state else 'disabled'} globally",
    )


@router.post(
    "/upload",
    responses={400: {"model": ErrorResponse}},
)
async def upload_document(req: RagUploadRequest):
    """
    Chunk and index a text document.
    Content can be pasted from any source (PDF text, docs, notes).
    Rebuilds the BM25 index automatically after upload.
    """
    chunks = rag.chunk_text(req.content)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Content is too short or could not be chunked. Minimum ~50 characters."
        )
    doc_id = await save_rag_document(req.name, chunks)
    await rag.rebuild_index()
    logger.info("RAG document uploaded: '%s' → %d chunks", req.name, len(chunks))
    return {
        "doc_id": doc_id,
        "name": req.name,
        "chunks_created": len(chunks),
        "message": f"Document indexed successfully into {len(chunks)} chunks",
    }


@router.get("/documents")
async def list_documents():
    """List all indexed RAG documents."""
    docs = await get_rag_documents()
    return {"data": docs, "count": len(docs)}


@router.delete(
    "/documents/{doc_id}",
    responses={404: {"model": ErrorResponse}},
)
async def delete_document(doc_id: str):
    """Delete a document and all its chunks. Rebuilds index automatically."""
    deleted = await delete_rag_document_db(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    await rag.rebuild_index()
    return {"status": "deleted", "doc_id": doc_id}
