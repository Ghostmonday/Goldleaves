#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip uv
if [[ -f "requirements.txt" ]]; then
  uv pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
  uv sync || pip install -e .
fi
uvicorn routers.main:app --reload --port 8000
