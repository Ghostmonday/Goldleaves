#requires -version 5
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip uv
if (Test-Path requirements.txt) {
  uv pip install -r requirements.txt
} elseif (Test-Path pyproject.toml) {
  uv sync
  if (!$?) { pip install -e . }
}
uvicorn routers.main:app --reload --port 8000
