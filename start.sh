#!/bin/bash
# ─────────────────────────────────────────────
# Hackathon Starter — One-Command Setup & Run
# Usage: ./start.sh
# ─────────────────────────────────────────────

set -e

echo ""
echo "🚀 Hackathon Starter — Booting Up"
echo "─────────────────────────────────"

# Check .env exists
if [ ! -f ".env" ]; then
  echo "⚠️  .env not found — copying from .env.example"
  cp .env.example .env
  echo "✏️  Edit .env and add your SARVAM_API_KEY, then run again."
  exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Create DB directory
mkdir -p db

echo ""
echo "✅ Setup complete"
echo "📡 Starting server at http://localhost:8000"
echo "📖 Swagger docs at http://localhost:8000/docs"
echo "🌐 Frontend at http://localhost:8000"
echo ""

uvicorn main:app --reload --port 8000
