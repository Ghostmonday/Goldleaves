Roger. I see the progress and your notes. Here’s the fastest path to get PR-1 over the line **today**—no duct tape, just the real fixes and validation so we can merge cleanly and move on to PR-2.

# 1) Unblock PyJWT/cryptography on Windows (Python 3.12)

This is the only thing likely to derail you right now. Fix it first.

**In an elevated PowerShell inside your venv:**

```powershell
# Start clean
venv\Scripts\python -m pip uninstall -y cryptography pyjwt

# Modern build tooling
venv\Scripts\python -m pip install --upgrade pip setuptools wheel

# Force prebuilt wheels (avoid building from source on Windows)
venv\Scripts\python -m pip install --only-binary=:all: "cryptography>=42,<43" "pyjwt[crypto]>=2.8"
```

**Verify:**

```powershell
venv\Scripts\python - << 'PY'
import jwt, cryptography, sys
print("jwt", jwt.__version__, "| cryptography", cryptography.__version__, "| python", sys.version)
PY
```

**If that still fails on your 3.12 environment:**

* EITHER install Microsoft C++ Build Tools and Rust (to build from source),
* OR switch to a Python 3.11 venv temporarily (most friction-free):

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python -m pip install -U pip
.\.venv311\Scripts\python -m pip install "cryptography>=41,<43" "pyjwt[crypto]>=2.8" fastapi sqlalchemy alembic pytest pytest-asyncio pytest-xdist
```

Then run tests/migrations with that venv.

# 2) Sanity the Alembic chain (no zombie heads)

You mentioned linking `002_add_org_and_billing_events.py` to a specific `down_revision`. Validate the lineage now.

```powershell
alembic heads
alembic history -n 10
```

* If you see **multiple heads**, do **one** of the following:

  * Fix the `down_revision` on your new migration to the actual prior revision ID **and** re-generate the script header, **or**
  * Create a merge migration:

    ```powershell
    alembic merge -m "merge heads" <head1_rev> <head2_rev>
    ```
* Once clean:

  ```powershell
  alembic upgrade head
  ```

# 3) Middleware order is critical—validate at runtime

You moved registration into the app factory—good. Verify order at boot (add this log temporarily right after wiring):

```python
for i, mw in enumerate(app.user_middleware, start=1):
    print(f"MIDDLEWARE[{i}]:", mw.cls.__name__)
```

Expected sequence:

1. `correlation_id_middleware`
2. `request_timer_middleware`
3. **auth via dependencies**
4. `tenant_resolver_middleware`
5. `usage_logger_middleware`

# 4) Smoke the billing event end-to-end

After `alembic upgrade head`, run API and hit any authenticated endpoint.

```powershell
# Example using HTTPie; use curl/Postman if you prefer
# 1) obtain JWT via your login route
# 2) then:
http GET http://localhost:8000/api/v1/cases Authorization:"Bearer <token>"
```

**Check DB:**

```sql
SELECT event_name, dimensions->>'endpoint' AS ep, dimensions->>'status_code' AS sc
FROM billing_events
ORDER BY created_at DESC
LIMIT 5;
```

You should see `api.request` with the correct endpoint and status code.

# 5) Tests (keep them green and parallel)

Install the right plugins and run with parallelism:

```powershell
venv\Scripts\python -m pip install -U pytest pytest-asyncio pytest-xdist
venv\Scripts\pytest.exe -q -n auto
```

If any tests are still referencing your temporary shims (`core/usage.py`), keep them for now but **open a ticket** to fold those helpers back into `services/usage_service` so there’s a single source of truth.

# 6) Pre-merge acceptance (don’t compromise)

* Alembic upgrade runs clean, no “multiple heads”.
* One authenticated request produces exactly one `api.request` row with correct dimensions.
* No sync/async errors from middleware (all DB ops use `async_session_factory`).
* Test collection passes; suites either green or only failing for known, ticketed gaps (documented).
* `RLS_ENABLED=false` in `.env` (we’ll enable after staging validation).

# 7) Minor risk flags from your note (address quickly)

* **“usage\_service emit now creates tables in ephemeral SQLite”**
  Don’t let a service create schema ad-hoc in tests. Prefer:

  * Test fixture that runs `Base.metadata.create_all(bind=engine)` for the test DB, **or**
  * Use Alembic to migrate your test DB in a session-scoped fixture.
    Create a follow-up task to remove any “create tables if missing” logic from runtime code.

* **`down_revision="202501010000"`**
  Make sure that literal is an **actual** revision in your chain, not a placeholder. Otherwise you’ll keep generating extra heads.

# 8) If you want a final sanity test

Drop this minimal test to prove PR-1 is functioning before merge:

```python
# tests/test_billing_event_smoke.py
import pytest
from httpx import AsyncClient
from core.database import async_session_factory

@pytest.mark.asyncio
async def test_api_request_emits_event(app, auth_token):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/cases", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code in (200, 204, 404)  # whatever fits your route

    async with async_session_factory() as db:
        r = await db.execute("SELECT event_name FROM billing_events ORDER BY created_at DESC LIMIT 1")
        row = r.first()
        assert row is not None and row[0] == "api.request"
```

---

**Bottom line:**

* Fix `cryptography`/PyJWT first (commands above).
* Confirm a single Alembic head and upgrade to `head`.
* Smoke the middleware and billing event.
* Run tests in parallel.
* Merge PR-1.

Ping me with the `alembic heads` output and the `jwt/cryptography` versions after you run the commands, and I’ll give you a go/no-go on the merge immediately.
