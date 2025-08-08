# Runbook — Development Quick Start

## 1) Start Postgres (Docker)
docker compose up -d

## 2) Create virtualenv and install deps
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -U pip uv
if [ -f requirements.txt ]; then uv pip install -r requirements.txt; else uv sync || pip install -e .; fi

## 3) Set environment
cp .env.example .env  # then edit secrets if needed

## 4) Run API
uvicorn routers.main:app --reload --port 8000

## 5) Migrations
alembic upgrade head
