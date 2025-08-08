
# Goldleaves — VS Code Onboarding

This repo is prepped for clean development with strict typing, linting, and one-click run.

## Quick Start (Windows)
1. Open the folder in VS Code.
2. Press `Ctrl+Shift+B` and run **Create venv (uv)**.
3. Then run **Install deps (uv)**.
4. Press `F5` and select **API: Uvicorn** to launch the server.
   - Entrypoint: `routers/main.py` (`routers.main:app`)
5. Create a `.env` from `.env.example` and set your `DATABASE_URL` and secrets.
6. Run qa tasks anytime:
   - **Tests (pytest)**
   - **Lint (ruff)** / **Format (ruff)**
   - **Type check (mypy)**

## Quick Start (macOS/Linux)
```bash
./run_dev.sh
```

## Tasks Palette
- **Create venv (uv)** — creates `.venv` and installs `uv`/`pip`.
- **Install deps (uv)** — installs project deps (prefers `requirements.txt`, falls back to `pyproject.toml`).
- **Run API (uvicorn)** — runs FastAPI on http://localhost:8000
- **Tests (pytest)** — runs tests quietly.
- **Lint/Format (ruff)** — fast lint + formatting.
- **Type check (mypy)** — static analysis.

## Launch Config
- **API: Uvicorn** — Debugger-attached server using `uvicorn routers.main:app --reload`

## Quality Gates
- **ruff.toml**, **mypy.ini**, **pytest.ini**, **.editorconfig** are provided.
- Optional: `pre-commit install` to enforce checks on each commit.

## Notes
- Keep `.env` in workspace root. Align keys with `.env.example`.
- If VS Code flags missing interpreter, choose `.venv` via Command Palette → *Python: Select Interpreter*.
