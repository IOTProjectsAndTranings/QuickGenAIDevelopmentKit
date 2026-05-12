# 🚀 Quick GenAI Development Kit — Final

> GenAI skeleton — swap domain in 30 minutes, not 3 hours.
> Based on: https://github.com/IOTProjectsAndTranings/QuickGenAIDevelopmentKit

---

## Quick Start

```bash
cp .env.example .env          # Add SARVAM_API_KEY and APP_API_KEY
./start.sh                    # One command — installs deps & runs
```

- App UI:     http://localhost:8000
- Swagger:    http://localhost:8000/docs
- Press **F5** in VS Code to run with debugger

---

## On Hackathon Day — 3 Files to Change

| File | What to change | Time |
|---|---|---|
| `services/mock_data.py` | Replace `DOMAIN_ENTITIES` with your problem's data | 20 min |
| `routers/ai.py` | Update `DOMAIN_NAME` + system prompt | 5 min |
| `frontend/index.html` | Update `APP_TITLE` + quick prompts | 5 min |

**Everything else stays identical.**

---

## Project Structure

```
QuickGenAIDevelopmentKit/
├── main.py                     # FastAPI entry — do not touch
├── config.py                   # Settings from .env — do not touch
├── requirements.txt
├── start.sh
│
├── services/
│   ├── LLM.py                  # LLM wrapper (Sarvam AI) — do not touch
│   ├── mcp_tools.py            # ✏️ Tool definitions — swap per problem
│   ├── mock_data.py            # ✏️ Domain data — swap per problem
│   ├── rag.py                  # RAG engine (BM25) — do not touch
│   ├── cache.py                # Response cache — do not touch
│   ├── rate_limiter.py         # Rate limiting — do not touch
│   └── database.py             # SQLite — do not touch
│
├── routers/
│   ├── ai.py                   # ✏️ AI routes — update DOMAIN_NAME
│   ├── data.py                 # Data routes
│   └── rag.py                  # RAG routes — do not touch
│
├── models/schemas.py           # Pydantic models
├── frontend/index.html         # React chat UI with RAG toggle
├── db/                         # SQLite DB lives here (auto-created)
├── tests/api.http              # VS Code REST client tests
├── architecture/diagram.html   # Architecture diagram
└── presentation/               # Phase 2 PPT template
```

---

## LLM Configuration (from repo)

| Setting | Value |
|---|---|
| Provider | Sarvam AI |
| Base URL | `https://api.sarvam.ai/v1` |
| Model | `sarvam-30b` |
| File | `services/LLM.py` |

---

## RAG — Knowledge Base Feature

Upload domain documents → they get chunked and indexed → LLM retrieves relevant excerpts automatically.

**Upload:** sidebar `📚 RAG` tab → paste text → Upload & Index

**Per message:** click `📚 RAG off` in input bar → turns blue → message uses knowledge base

**Global toggle:** toggle switch in RAG sidebar tab

**On response:** `📚 RAG ×3` badge = RAG was used, `💾 cached` = from cache

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | System + LLM status |
| POST | `/api/ai/chat` | MCP tool-calling LLM chat |
| POST | `/api/ai/feedback` | 👍👎 Feedback (judging criteria) |
| POST | `/api/ai/translate` | Sarvam translation |
| GET | `/api/ai/cache/stats` | Cache statistics |
| DELETE | `/api/ai/cache` | Clear cache |
| GET | `/api/data/entities` | All domain entities |
| GET | `/api/data/entities/by-status/{s}` | Filter by status |
| GET | `/api/data/entities/{id}` | Single entity |
| GET | `/api/data/alerts` | Active alerts |
| GET | `/api/data/history` | Chat history (max 100) |
| GET | `/api/rag/status` | RAG status + stats |
| POST | `/api/rag/toggle` | Enable/disable RAG globally |
| POST | `/api/rag/upload` | Upload & index a document |
| GET | `/api/rag/documents` | List indexed documents |
| DELETE | `/api/rag/documents/{id}` | Delete a document |

All `/api/*` routes require `X-API-Key` header.

---

## What Was Fixed (v2 → Final)

| # | Issue | Fix |
|---|---|---|
| Repo | `sarvam.py` → `LLM.py` | Provider-agnostic naming |
| Repo | Base URL `→ /v1` endpoint | Correct Sarvam API URL |
| Repo | Model `→ sarvam-30b` | Upgraded model |
| Repo | `db/` folder in repo | DB directory tracked |
| C1 | `[cached]` in UI | `cache_hit: bool` flag + 💾 badge |
| C2 | Route conflict | `/by-status/` before `/{id}` |
| C3 | Dead import | Removed unused `build_llm_context` |
| C4 | None API key | Raises `ValueError` at startup |
| H1 | Health burns credits | 60s cached health result |
| H2 | Double function calls | Store in variable first |
| H3 | `rating=0` allowed | `Literal[-1, 1]` type |
| H4 | No `response_id` check | `response_id_exists()` validates |
| H5 | Unlimited history | `Query(le=100)` max |
| H6 | IoT text in prompt | Removed domain-specific line |
| M1–M7 | Medium issues | All fixed |
| L1–L7 | Low issues | All fixed |
| NEW | RAG feature | BM25 retrieval, toggleable per-message |

---

## Security Checklist

- [x] No hardcoded secrets — all via `.env`
- [x] `.env` in `.gitignore`
- [x] `APP_API_KEY` validated at startup — no default
- [x] `SARVAM_API_KEY` validated at startup — no default
- [x] API key header auth on all `/api/*` routes
- [x] Rate limiting — 30 req/min per IP
- [x] Feedback `response_id` validated before saving
- [x] Input validation via Pydantic throughout
- [x] Full UUID primary keys — no collision risk

---

## Google Drive Submission Structure

```
/Hackathon_TeamName/
├── code/
│   └── QuickGenAIDevelopmentKit.zip   (this project)
├── presentation/
│   └── Hackathon_Phase2.pptx
├── demo/
│   └── demo_video.mp4                 (optional)
└── README.txt                         (team name, members, problem chosen)
```
