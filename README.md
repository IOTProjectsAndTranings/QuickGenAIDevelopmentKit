# 🚀 Quick GenAI Development Kit


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

##  3 Files to Change as per your Problem statement

| File | What to change | Time |
|---|---|---|
| `services/mock_data.py` | Replace `DOMAIN_ENTITIES` with your problem's data | 20 min |
| `routers/ai.py` | Update `DOMAIN_NAME` + system prompt | 5 min |
| `frontend/index.html` | Update `APP_TITLE` + quick prompts | 5 min |


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


