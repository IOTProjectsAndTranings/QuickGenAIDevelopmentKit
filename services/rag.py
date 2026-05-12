"""
services/rag.py
────────────────
RAG (Retrieval Augmented Generation) engine.
Pure Python BM25 retrieval — zero extra dependencies.

Features:
  - Globally toggleable at runtime via toggle() / set_enabled()
  - Per-request opt-in via use_rag flag in ChatRequest
  - Documents chunked on upload and stored in SQLite
  - BM25 index is in-memory, rebuilt from DB on startup and on doc changes
  - build_rag_context() returns formatted text injected into LLM prompt

On hackathon day:
  - Upload domain PDFs / docs via UI or POST /api/rag/upload
  - Toggle on/off in the chat UI per message OR globally
  - Zero code changes needed
"""

import logging
import math
import re
import time
from collections import Counter, defaultdict

from config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RAG_TOP_K, RAG_ENABLED_DEFAULT

logger = logging.getLogger(__name__)

# ── Global toggle ─────────────────────────────────────────────────────────────
_rag_enabled: bool = RAG_ENABLED_DEFAULT


def is_enabled() -> bool:
    return _rag_enabled


def toggle() -> bool:
    global _rag_enabled
    _rag_enabled = not _rag_enabled
    logger.info("RAG globally %s", "enabled" if _rag_enabled else "disabled")
    return _rag_enabled


def set_enabled(state: bool) -> None:
    global _rag_enabled
    _rag_enabled = state


# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = RAG_CHUNK_SIZE,
    overlap: int = RAG_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks at sentence boundaries.
    Returns list of chunk strings. Filters out chunks shorter than 20 chars.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current: list[str] = []
    current_len: int = 0

    for sentence in sentences:
        slen = len(sentence)
        if current_len + slen > chunk_size and current:
            chunk = " ".join(current)
            chunks.append(chunk)
            # Carry overlap forward
            overlap_buf: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) < overlap:
                    overlap_buf.insert(0, s)
                    overlap_len += len(s) + 1
                else:
                    break
            current = overlap_buf
            current_len = overlap_len

        current.append(sentence)
        current_len += slen + 1

    if current:
        chunks.append(" ".join(current))

    return [c.strip() for c in chunks if len(c.strip()) > 20]


# ── BM25 index ────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


class _BM25Index:
    """In-memory BM25 index over RAG chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._corpus: list[tuple[str, list[str]]] = []   # (chunk_id, tokens)
        self._texts: dict[str, str] = {}                  # chunk_id → raw text
        self._idf: dict[str, float] = {}
        self._avg_dl: float = 1.0

    def build(self, chunks: list[tuple[str, str]]) -> None:
        """Rebuild index from (chunk_id, chunk_text) pairs."""
        self._texts = {cid: text for cid, text in chunks}
        self._corpus = [(cid, _tokenize(text)) for cid, text in chunks]
        N = len(self._corpus)
        if N == 0:
            self._avg_dl = 1.0
            self._idf = {}
            logger.info("RAG index cleared (no documents)")
            return
        self._avg_dl = sum(len(toks) for _, toks in self._corpus) / N
        df: dict[str, int] = defaultdict(int)
        for _, toks in self._corpus:
            for term in set(toks):
                df[term] += 1
        self._idf = {
            term: math.log((N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }
        logger.info("RAG index built: %d chunks across %d unique terms", N, len(self._idf))

    def search(self, query: str, top_k: int = RAG_TOP_K) -> list[tuple[str, str, float]]:
        """Returns (chunk_id, chunk_text, score) sorted by score desc."""
        if not self._corpus:
            return []
        q_tokens = _tokenize(query)
        results: list[tuple[str, str, float]] = []
        for chunk_id, tokens in self._corpus:
            dl = len(tokens)
            tf = Counter(tokens)
            score = sum(
                self._idf.get(term, 0)
                * (tf[term] * (self.k1 + 1))
                / (tf[term] + self.k1 * (1 - self.b + self.b * dl / self._avg_dl))
                for term in q_tokens
                if term in tf
            )
            if score > 0:
                results.append((chunk_id, self._texts.get(chunk_id, ""), score))
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    @property
    def doc_count(self) -> int:
        return len(self._corpus)


_index = _BM25Index()


async def rebuild_index() -> None:
    """Reload all chunks from DB and rebuild the BM25 index."""
    from services.database import get_all_rag_chunks
    chunks = await get_all_rag_chunks()
    _index.build(chunks)


def search(query: str, top_k: int = RAG_TOP_K) -> list[tuple[str, str, float]]:
    """Search the current index. Returns (chunk_id, text, score)."""
    return _index.search(query, top_k)


def build_rag_context(query: str, top_k: int = RAG_TOP_K) -> tuple[str, int]:
    """
    Retrieve top-k chunks and format as LLM context string.
    Returns (context_string, chunks_used_count).
    Returns ("", 0) if no results or RAG disabled.
    """
    if not _rag_enabled:
        return "", 0
    results = _index.search(query, top_k)
    if not results:
        return "", 0
    lines = [
        "── Knowledge Base Context ──────────────────────────────",
        "Use the excerpts below to answer accurately.",
        "If the answer is not in the excerpts, say so.",
        "",
    ]
    for i, (_, text, _score) in enumerate(results, 1):
        lines.append(f"[Excerpt {i}]")
        lines.append(text)
        lines.append("")
    lines.append("── End of Knowledge Base Context ───────────────────────")
    return "\n".join(lines), len(results)


def index_stats() -> dict:
    return {
        "enabled": _rag_enabled,
        "indexed_chunks": _index.doc_count,
    }
