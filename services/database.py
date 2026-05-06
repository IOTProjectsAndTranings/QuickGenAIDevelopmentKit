"""
services/database.py
────────────────────
Lightweight SQLite via aiosqlite.
Stores chat history + feedback — both are judging criteria.
"""

import aiosqlite
import time
import uuid
from config import DB_PATH


async def init_db():
    """Run once at startup to create tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_log (
                id          TEXT PRIMARY KEY,
                prompt      TEXT NOT NULL,
                response    TEXT NOT NULL,
                created_at  REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id          TEXT PRIMARY KEY,
                response_id TEXT NOT NULL,
                rating      INTEGER NOT NULL,   -- 1 = thumbs up, -1 = thumbs down
                created_at  REAL NOT NULL
            )
        """)
        await db.commit()


async def save_chat(prompt: str, response: str) -> str:
    """Save a chat exchange. Returns the response_id."""
    response_id = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_log VALUES (?, ?, ?, ?)",
            (response_id, prompt, response, time.time())
        )
        await db.commit()
    return response_id


async def save_feedback(response_id: str, rating: int):
    """Save user feedback on an AI response."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO feedback VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4())[:8], response_id, rating, time.time())
        )
        await db.commit()


async def get_chat_history(limit: int = 20):
    """Fetch recent chat history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM chat_log ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
