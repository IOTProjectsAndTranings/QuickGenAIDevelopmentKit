"""
services/database.py
────────────────────
SQLite via aiosqlite.
Tables: chat_log, feedback, rag_documents, rag_chunks

Fixes applied:
  - Full UUID primary keys (no collision risk)
  - UNIQUE constraint on feedback(response_id)
  - RAG tables added
  - response_id_exists() for feedback validation
"""

import aiosqlite
import logging
import time
import uuid
from config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db():
    """Create all tables at startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_log (
                id         TEXT PRIMARY KEY,
                prompt     TEXT NOT NULL,
                response   TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id          TEXT PRIMARY KEY,
                response_id TEXT NOT NULL UNIQUE,
                rating      INTEGER NOT NULL,
                created_at  REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at  REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id          TEXT PRIMARY KEY,
                doc_id      TEXT NOT NULL,
                chunk_text  TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                created_at  REAL NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES rag_documents(id)
            )
        """)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


# ── Chat log ──────────────────────────────────────────────────────────────────

async def save_chat(prompt: str, response: str) -> str:
    """Save a chat exchange. Returns full UUID as response_id."""
    response_id = str(uuid.uuid4())      # Fix L4: full UUID, no collision risk
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_log VALUES (?, ?, ?, ?)",
            (response_id, prompt, response, time.time())
        )
        await db.commit()
    return response_id


async def get_chat_history(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM chat_log ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ── Feedback ──────────────────────────────────────────────────────────────────

async def response_id_exists(response_id: str) -> bool:
    """Check response_id exists before saving feedback."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM chat_log WHERE id = ?", (response_id,)
        )
        return await cursor.fetchone() is not None


async def save_feedback(response_id: str, rating: int):
    """Save or replace feedback. UNIQUE on response_id prevents duplicates."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO feedback VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), response_id, rating, time.time())
        )
        await db.commit()


# ── RAG documents ─────────────────────────────────────────────────────────────

async def save_rag_document(name: str, chunks: list[str]) -> str:
    """Store a document and its chunks. Returns doc_id."""
    doc_id = str(uuid.uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO rag_documents VALUES (?, ?, ?, ?)",
            (doc_id, name, len(chunks), time.time())
        )
        for i, chunk_text in enumerate(chunks):
            await db.execute(
                "INSERT INTO rag_chunks VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), doc_id, chunk_text, i, time.time())
            )
        await db.commit()
    logger.info("Saved RAG document '%s' with %d chunks", name, len(chunks))
    return doc_id


async def delete_rag_document_db(doc_id: str) -> bool:
    """Delete a document and its chunks. Returns False if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM rag_documents WHERE id = ?", (doc_id,)
        )
        if not await cursor.fetchone():
            return False
        await db.execute("DELETE FROM rag_chunks WHERE doc_id = ?", (doc_id,))
        await db.execute("DELETE FROM rag_documents WHERE id = ?", (doc_id,))
        await db.commit()
    logger.info("Deleted RAG document %s", doc_id)
    return True


async def get_rag_documents() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM rag_documents ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_rag_chunks() -> list[tuple[str, str]]:
    """Return all (chunk_id, chunk_text) pairs for index building."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, chunk_text FROM rag_chunks")
        rows = await cursor.fetchall()
        return [(row[0], row[1]) for row in rows]
