# 🚀 Hackathon AI Starter

> GenAI skeleton — swap domain in 30 minutes, not 3 hours.

---

## Quick Start

```bash
# 1. Clone / unzip this folder
# 2. Copy env file
cp .env.example .env

# 3. Add your Sarvam API key to .env

# 4. Run
./start.sh

# App runs at:  http://localhost:8000
# Swagger docs: http://localhost:8000/docs
# Frontend:     http://localhost:8000
```

Or press **F5** in VS Code (venv must exist first).

---

## On Hackathon Day — 3 Files to Change

| File | What to Change | Time |
|---|---|---|
| `services/mock_data.py` | Replace `DOMAIN_ENTITIES` with your problem's data | 20 min |
| `routers/ai.py` | Update `SYSTEM_PROMPT_TEMPLATE` domain name | 5 min |
| `frontend/index.html` | Update `APP_TITLE` and quick prompts | 5 min |

**Everything else stays identical.**

---

## Project Structure

```
hackathon-starter/
├── main.py               # FastAPI app — do not touch
├── config.py             # Settings from .env — do not touch
├── requirements.txt      # Dependencies
├── start.sh              # One-command run
│
├── routers/
│   ├── ai.py             # /api/ai/* — chat, feedback, translate
│   └── data.py           # /api/data/* — entities, alerts, history
│
├── services/
│   ├── sarvam.py         # Sarvam AI wrapper — do not touch
│   ├── mock_data.py      # ✏️ CHANGE THIS per problem
│   └── database.py       # SQLite — do not touch
│
├── models/
│   └── schemas.py        # Pydantic models
│
├── frontend/
│   └── index.html        # Full React UI — single file
│
├── tests/
│   └── api.http          # VS Code REST client tests
│
└── .vscode/
    ├── launch.json        # F5 to run
    └── settings.json      # Editor config
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | System + Sarvam status |
| POST | `/api/ai/chat` | LLM chat with domain context |
| POST | `/api/ai/feedback` | 👍👎 feedback (judging criteria) |
| POST | `/api/ai/translate` | Sarvam translation |
| GET | `/api/data/entities` | All domain entities |
| GET | `/api/data/entities/{id}` | Single entity |
| GET | `/api/data/entities/status/{s}` | Filter by status |
| GET | `/api/data/alerts` | Active alerts |
| GET | `/api/data/history` | Chat history |

All `/api/*` routes require `X-API-Key` header.

---

## Security Checklist

- [x] No hardcoded secrets — all via `.env`
- [x] `.env` in `.gitignore`
- [x] API key header auth on all routes
- [x] Error handling — all routes wrapped in try/except
- [x] Input validation via Pydantic
- [x] Feedback stored in SQLite (judges check for this)

---

## Judging Criteria Coverage

| Criterion | How it's covered |
|---|---|
| Working prototype | FastAPI + React running out of box |
| Sarvam AI integration | `services/sarvam.py` wraps all APIs |
| Feedback mechanism | `/api/ai/feedback` + 👍👎 in UI |
| Security | API key auth + .env secrets |
| UI / usability | Responsive React chat interface |
| Scalability | Async FastAPI, SQLite → swap Postgres easily |
| Architecture | Clean layered structure with separation of concerns |
