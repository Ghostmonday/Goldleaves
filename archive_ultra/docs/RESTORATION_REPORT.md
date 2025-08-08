# Goldleaves — Restoration & Integrity Report (2025-08-08T10:54:14.486174Z)

## Topline Status
- Files scanned: **331**
- Python files audited: **262** OK, **3** issues
- FastAPI entrypoint candidates: **57**
- `pyproject.toml` detected: **yes**
- Docker Compose detected: **yes**
- Alembic detected: **yes**
- __init__.py added for packages: **4**

## Syntax Findings (must-fix)
- ✅ All Python files parsed without syntax errors.
## FastAPI Entrypoints Detected
- `api/v1/auth.py` — apps: app variable not inferred
- `api/v1/documents.py` — apps: app variable not inferred
- `api/v1/organizations.py` — apps: app variable not inferred
- `api/v1/users.py` — apps: app variable not inferred
- `api/v1/__init__.py` — apps: app variable not inferred
- `app/dependencies.py` — apps: app variable not inferred
- `app/main.py` — apps: app, app
- `app/routers/legal_chat.py` — apps: app variable not inferred
- `apps/backend/main.py` — apps: app
- `apps/backend/api/routers/auth.py` — apps: app variable not inferred
- `apps/backend/api/routers/ping.py` — apps: app variable not inferred
- `apps/backend/api/routers/token_refresh.py` — apps: app variable not inferred
- `apps/backend/api/routers/verification/token_confirm.py` — apps: app variable not inferred
- `apps/backend/api/routers/verification/token_resend.py` — apps: app variable not inferred
- `apps/backend/api/routers/verification/token_send.py` — apps: app variable not inferred
- `apps/backend/api/routers/verification/__init__.py` — apps: app variable not inferred
- `core/dependencies.py` — apps: app variable not inferred
- `core/email_utils.py` — apps: app variable not inferred
- `core/exceptions.py` — apps: app variable not inferred
- `models/auth_router.py` — apps: app variable not inferred
- ... and 37 more

## Project Configuration Snapshot
- Name: **gold-leaves-api**
- Python requires: **^3.11**
- Dependencies (preview): python, fastapi, uvicorn, pydantic, sqlalchemy, psycopg2-binary, alembic, passlib, python-jose, python-dotenv

## Environment Variables Audit
- Keys in `.env.example` missing in `.env`: ENVIRONMENT, DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, VERIFICATION_TOKEN_EXPIRE_HOURS, RESET_TOKEN_EXPIRE_HOURS, ALLOWED_ORIGINS, DEBUG, ENABLE_DOCS
- Extra keys in `.env` not documented in `.env.example`: database_url, jwt_secret, jwt_algorithm, jwt_expiration_minutes, environment, debug, app_name, allowed_origins, verification_token_expire_hours, reset_token_expire_hours

## Alembic / DB Migrations
- Alembic versions detected: **3**

## Changes Applied (Restoration)
- Added `__init__.py` to `app/guardrails/__init__.py`
- Added `__init__.py` to `app/routers/__init__.py`
- Added `__init__.py` to `collected_files/__init__.py`
- Added `__init__.py` to `examples/__init__.py`

## Next Actions (recommended)
1) Run `uv sync` or `pip install -e .` to materialize dependencies as defined in `pyproject.toml`.
2) Validate `DATABASE_URL` and secrets in `.env`; update `.env.example` to match if keys were added.
3) Start locally via Docker Compose or `uvicorn` using the main FastAPI entrypoint (see candidates above).
4) Run Alembic migrations (`alembic upgrade head`) if a fresh DB is needed.
5) Execute your test suite (if present) and smoke-test all routers (auth, client, case, etc.).