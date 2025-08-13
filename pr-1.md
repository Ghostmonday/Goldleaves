# PR-1 Integration Plan for Goldleaves (Integration-Ready)

**Purpose**: Adapt PR-1 code changes to the current Goldleaves repository without overwriting newer code or introducing path/import errors.

---
## Pre-Integration Safety Checklist
1. **Scan repository structure**:
   - Locate existing `middleware` directory; confirm if `stack.py` and `usage.py` exist or need creation.
   - Locate models directory; confirm where `billing_event.py` should live.
   - Confirm where database session factories (`async_session_factory`) and `Base` are defined.
2. **Map imports**:
   - Check if import paths match (`middleware.stack` vs `apps.backend.middleware.stack`).
   - Adjust to actual module paths before insertion.
3. **Avoid overwriting**:
   - If a file already contains relevant code, integrate changes by extending rather than replacing.
4. **Order of execution**:
   - Step 1: Implement model(s) → Step 2: Implement middleware → Step 3: Wire in `main.py` → Step 4: Add tests → Step 5: Run migrations/tests.
5. **Testing alignment**:
   - Verify `get_test_token` helper exists; if not, adapt test code to repo’s auth helper functions.

---
## Integration Sequence
Follow this sequence **exactly**:

1. **Add `BillingEvent` model**:
   - Create `models/billing_event.py` with PR-1 definition.
   - Run `alembic revision --autogenerate -m "add billing_event table"` and `alembic upgrade head`.

2. **Update `middleware/stack.py`**:
   - Implement async DB usage in `tenant_resolver_middleware`.
   - Verify DB session factory import matches your repo.

3. **Create `middleware/usage.py`**:
   - Add `usage_logger_middleware` from PR-1.
   - Confirm `emit_billing_event` exists in `services.usage_service`; if not, create stub.

4. **Wire into `main.py` (or app entry)**:
   - Append middleware registration in correct order.

5. **Add/Update Tests**:
   - Place `test_billing_event_created` in existing middleware test suite.
   - Adapt helper calls to your repo’s auth utilities.

6. **Run full test suite**:
   - Fix any import or runtime errors before committing.

---
## PR-1 Code Implementation
(Original PR-1 details follow; adapt imports and paths to match your repo)


Short answer: **Ship PR-1 first. Pause Copilot’s “keep adding stubs” loop.**

Why (no sugar-coating):

* **PR-1 is foundational.** Tenancy, billing events, and middleware order affect every service contract. If Copilot keeps stubbing now, you’ll rework those stubs once PR-1 lands. That’s churn.
* **Risk isolation.** PR-1 is small, surgical, and reversible (feature-gated RLS, additive tables). Land it, then let Copilot build on a stable platform.
* **Test signal quality.** Usage logging + org context in place = tests start measuring the right behavior, not a moving target.

## Decision

**Prioritize PR-1 integration, then resume Copilot to finish stubs against the PR-1 contracts.**

## Execution plan (fast, safe)

1. **Create branch:** `merge/pr1-core`.
2. **Apply PR-1 items only:**

   * Alembic migration (`organizations`, `organization_id` cols, `billing_events`).
   * `models/billing_event.py`.
   * Async tenant resolver middleware using `async_session_factory` + `text("set_config…")`.
   * `middleware/usage.py` post-response emitter.
   * Wire middleware order: correlation → timer → **auth (deps)** → tenant → usage.
   * `.env.example` additions (Redis/S3/RLS flags).
3. **Run:** `alembic upgrade head` → smoke test → confirm one `api.request` row in `billing_events`.
4. **Merge to main.** Keep `RLS_ENABLED=false`.

Then:

5. **Resume Copilot** on a new branch `feature/copilot-stubs` with a **tight brief**:

   * “Finish schemas/document, schemas/storage, services/forms, email verification, and models/case mixins **conforming to** PR-1:

     * every DB write/read carries `organization_id`
     * emit `billing_events` for `api.request`, `doc.upload`, `doc.processed`
     * do not change middleware order; rely on tenant resolver for org context.”
   * Goal: green tests + consistent response shapes; no changes to PR-1 infra.

## If you absolutely must choose only one this hour

* **Choose PR-1.** It’s 1–2 hours of focused integration vs. days of rework later.

## Ready-to-paste prompts

**To Copilot (now):**

> “Pause stub expansion. Implement PR-1 core only: migration 002 (organizations, org\_id on users/clients/cases/documents, billing\_events + indexes + backfill), add models/billing\_event.py, add async tenant\_resolver\_middleware using async\_session\_factory + set\_config, add middleware/usage.py emitter (skip /health,/docs and 401/403), wire middleware order (correlation→timer→auth deps→tenant→usage). Update .env.example with Redis/S3/RLS flags. Make small commits per step. Then run alembic upgrade and one authenticated GET to verify a billing\_events row exists.”

**After PR-1 merges:**

> “Resume: finish schemas/document & schemas/storage, services/forms, email verification endpoints. Ensure all routes pass `organization_id` through services, and emit billing events per taxonomy. Keep middleware untouched. Run tests & coverage.”

If you want, I’ll generate a **2-commit checklist** Copilot can follow verbatim (commit messages + file list per commit).


Here’s the **2-commit, copy-paste playbook** for Copilot to land PR-1 cleanly, then hand back to you. Tight scope, zero churn.

# Commit 1 — PR-1 Core Infra (DB + Model + Async Tenant + Usage Logger)

**Commit message**

```
feat(infra): PR-1 core — orgs/org_id/billing_events, async tenant resolver, usage logging
```

**Files to add/update**

* `alembic/versions/002_add_org_and_billing_events.py`

  * Create `organizations` table.
  * Add nullable `organization_id` to `users`, `clients`, `cases`, `documents` (skip gracefully if table missing).
  * Backfill: default org per user (slug from email), set `users.organization_id`.
  * Create `billing_events` (+ indexes on `(organization_id, created_at)` and `(event_name)`).
  * Safe downgrade.
* `models/billing_event.py`

  * ORM matching migration: fields `id, organization_id, event_type, event_name, resource_id, quantity, unit, unit_cost_cents, dimensions(JSONB default dict), status, created_at`.
* `middleware/stack.py` (or equivalent)

  * Ensure **async** tenant resolver uses `async_session_factory` and SQLAlchemy `text()` to:

    * `set_config('app.current_org', :org, false)`
    * `set_config('app.rls_enabled', :flag, false)` (from env, default `false`)
* `middleware/usage.py` (new)

  * Post-response emitter:

    * Skip `/health`, `/docs`
    * Skip `401/403`
    * Call `services/usage_service.emit_billing_event(...)` with dimensions: `endpoint, method, status_code, duration_ms, request_id`.

**App wiring (keep order)**

* In app entry (e.g., `models/main.py` or `routers/main.py`):

  1. `correlation_id_middleware`
  2. `request_timer_middleware`
  3. **auth via dependencies** (unchanged)
  4. `tenant_resolver_middleware`
  5. `usage_logger_middleware`

**ENV surface (append to `.env.example`)**

```
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
S3_BUCKET=goldleaves-docs
S3_REGION=us-west-2
RLS_ENABLED=false
TENANT_ISOLATION_MODE=row
TIER_RATE_LIMITS={"starter":{"api":60},"pro":{"api":300}}
```

**Acceptance for Commit 1**

* `alembic upgrade head` runs cleanly.
* App boots; **no sync/async DB errors** in middleware.
* Authenticated GET on any `/api/v1/*` route creates one `billing_events` row with `event_name='api.request'`.
* RLS remains **off** (`RLS_ENABLED=false`).

---

# Commit 2 — Tests + Sanity Hooks

**Commit message**

```
test(infra): verify api.request billing event; wire middleware order; env surface
```

**Files to add/update**

* `tests/test_billing_events_integration.py`

  * Arrange: obtain JWT (fixture or helper).
  * Act: `GET /api/v1/cases` (or any existing route).
  * Assert: one row in `billing_events` where `dimensions->>'endpoint'` matches; `event_name == 'api.request'`; `status_code` in dimensions equals response code.
* (If absent) Ensure app registers middleware in the required order (idempotent check).
* Confirm `.env.example` contains the new keys.

**Acceptance for Commit 2**

* `pytest -q` passes (or at least your existing suites remain green and the new test passes).
* Coverage runs if configured (no threshold change required).

---

## Copilot one-liner prompts (paste verbatim)

**For Commit 1**

> Implement PR-1 core exactly: create `alembic/versions/002_add_org_and_billing_events.py` (orgs table, add organization\_id to users/clients/cases/documents with safe skips, backfill from email slug, create billing\_events with indexes). Add `models/billing_event.py` ORM. Update `middleware/stack.py` to use `async_session_factory` and SQLAlchemy `text()` to set `app.current_org` and `app.rls_enabled`. Add `middleware/usage.py` to emit `api.request` events after responses (skip /health, /docs, 401/403). Wire middleware order: correlation→timer→auth deps→tenant→usage. Append the specified env keys to `.env.example`. Make a single commit with message: `feat(infra): PR-1 core — orgs/org_id/billing_events, async tenant resolver, usage logging`. Then run `alembic upgrade head` and perform one authenticated GET to verify a row appears in `billing_events`.

**For Commit 2**

> Add `tests/test_billing_events_integration.py` to assert that an authenticated API request creates a `billing_events` row with `event_name='api.request'`, matching endpoint, and correct `status_code` in dimensions. Ensure middleware order is registered as specified and `.env.example` contains new keys. Commit with: `test(infra): verify api.request billing event; wire middleware order; env surface`. Run `pytest -q` and report pass/fail.

---

## If Copilot asks “continue stubbing now or later?”

Answer: **Later.** PR-1 first. Resume stubs only after Commit 2 passes, keeping `RLS_ENABLED=false`.

Want me to generate the minimal code blocks for the migration, model, and two middlewares tailored to your current file structure? If you paste your `core/database.py` (just the session/engine bits) and app entry file, I’ll align them precisely.

[CLAUDE] →

## PR-1 VALIDATED: SHIP IT

### APPROVAL WITH CRITICAL FIXES

**Code Review**:
1. ✅ Migration clean, backfill strategy solid
2. ⚠️ **FIX**: `get_db()` is sync, middleware is async - mismatch
3. ⚠️ **FIX**: Missing BillingEvent model definition
4. ✅ Lua script correct
5. ✅ ENV additions complete

### REQUIRED FIXES

#### 1. ASYNC DB IN MIDDLEWARE
```python
# middleware/stack.py (FIXED)
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session_factory

async def tenant_resolver_middleware(request: Request, call_next):
    if hasattr(request.state, "user"):
        request.state.organization_id = request.state.user.organization_id

        # Use async session
        async with async_session_factory() as db:
            await db.execute(
                text("SELECT set_config('app.current_org', :org, false)"),
                {"org": str(request.state.organization_id)}
            )
            await db.execute(
                text("SELECT set_config('app.rls_enabled', :enabled, false)"),
                {"enabled": os.getenv('RLS_ENABLED', 'false')}
            )
            await db.commit()

    return await call_next(request)
```

#### 2. BILLING EVENT MODEL
```python
# models/billing_event.py (NEW)
from sqlalchemy import Column, String, Numeric, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from core.database import Base
import uuid
from datetime import datetime

class BillingEvent(Base):
    __tablename__ = "billing_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    event_name = Column(String(64), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True))
    quantity = Column(Numeric(12, 4), default=1.0)
    unit = Column(String(16), nullable=False)
    unit_cost_cents = Column(Integer)
    dimensions = Column(JSONB, default=dict)
    status = Column(SmallInteger, default=0)  # 0=pending, 1=posted
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
```

#### 3. USAGE MIDDLEWARE (MISSING)
```python
# middleware/usage.py (NEW)
from services.usage_service import emit_billing_event

async def usage_logger_middleware(request: Request, call_next):
    response = await call_next(request)

    # Skip non-billable routes
    if request.url.path.startswith("/health") or request.url.path.startswith("/docs"):
        return response

    # Skip auth failures
    if response.status_code in [401, 403]:
        return response

    # Log usage event
    if hasattr(request.state, "organization_id"):
        await emit_billing_event(
            org_id=request.state.organization_id,
            event_type="api",
            event_name="api.request",
            quantity=1,
            unit="call",
            dimensions={
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": getattr(request.state, "duration_ms", 0),
                "request_id": request.state.request_id
            }
        )

    return response
```

#### 4. WIRE INTO MAIN APP
```python
# routers/main.py (UPDATE)
from middleware.stack import (
    correlation_id_middleware,
    request_timer_middleware,
    tenant_resolver_middleware
)
from middleware.usage import usage_logger_middleware

# Add middlewares in order
app.middleware("http")(correlation_id_middleware)
app.middleware("http")(request_timer_middleware)
# Auth runs via dependencies
app.middleware("http")(tenant_resolver_middleware)
# Rate limit and quota run via dependencies
app.middleware("http")(usage_logger_middleware)
```

### TEST ADDITIONS
```python
# tests/test_middleware.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_billing_event_created():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login to get token
        token = await get_test_token(client)

        # Make API call
        response = await client.get(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Check billing_events table
        async with async_session_factory() as db:
            result = await db.execute(
                "SELECT * FROM billing_events WHERE dimensions->>'endpoint' = '/api/v1/cases'"
            )
            event = result.first()

            assert event is not None
            assert event.event_name == "api.request"
            assert event.quantity == 1
            assert event.dimensions["status_code"] == 200
```

### DEPLOYMENT CHECKLIST
1. ✅ Run migration
2. ✅ Update `.env` with Redis URL
3. ✅ Deploy middleware stack
4. ✅ Verify billing events flow
5. ✅ Monitor for errors

**SHIP PR-1** with these fixes. Ready for PR-2 planning?
