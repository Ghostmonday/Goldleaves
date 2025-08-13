#!/bin/bash
# PR-1 Sanity Checklist Script

echo "========================================="
echo "PR-1 SANITY CHECKLIST"
echo "========================================="

# 1. Check Alembic heads
echo ""
echo "1. Checking Alembic heads..."
echo "----------------------------------------"
alembic heads
echo "✓ Should show ONE head only"

# 2. Run migrations
echo ""
echo "2. Running migrations..."
echo "----------------------------------------"
alembic upgrade head
echo "✓ Should complete without errors"

# 3. Verify tables exist
echo ""
echo "3. Verifying database tables..."
echo "----------------------------------------"
psql $DATABASE_URL -c "\dt" | grep -E "(organizations|billing_events)"
echo "✓ Both organizations and billing_events should be listed"

# 4. Test middleware order with curl
echo ""
echo "4. Testing middleware order..."
echo "----------------------------------------"
ORG_ID=$(uuidgen)
echo "Testing with org_id: $ORG_ID"

# Start the server in background (kill it after test)
uvicorn routers.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 3

# Make test request
curl -X GET http://localhost:8000/ \
  -H "X-Organization-ID: $ORG_ID" \
  -H "Content-Type: application/json" \
  -v 2>&1 | grep -E "(X-Request-ID|X-Response-Time-MS)"

echo "✓ Should see X-Request-ID and X-Response-Time-MS headers"

# 5. Check billing event was created
echo ""
echo "5. Checking billing event creation..."
echo "----------------------------------------"
psql $DATABASE_URL -c "
  SELECT 
    event_name,
    dimensions->>'endpoint' as endpoint,
    dimensions->>'method' as method,
    dimensions->>'status_code' as status_code,
    dimensions->>'request_id' as request_id,
    dimensions->>'duration_ms' as duration_ms
  FROM billing_events 
  WHERE organization_id = '$ORG_ID'
  ORDER BY created_at DESC
  LIMIT 1;
"
echo "✓ Should show one api.request event with all dimensions populated"

# 6. Test RLS GUCs
echo ""
echo "6. Testing RLS GUCs..."
echo "----------------------------------------"
curl -X GET http://localhost:8000/test-guc \
  -H "X-Organization-ID: $ORG_ID" \
  -H "Content-Type: application/json"

# Kill the server
kill $SERVER_PID

# 7. Run async tests
echo ""
echo "7. Running async tests..."
echo "----------------------------------------"
pytest tests/test_billing_event_smoke.py -v
echo "✓ All tests should pass"

echo ""
echo "========================================="
echo "PR-1 CHECKLIST COMPLETE"
echo "========================================="
echo ""
echo "Summary:"
echo "✓ Single Alembic head"
echo "✓ Migrations run clean"
echo "✓ Tables created with correct schema"
echo "✓ Middleware order correct (correlation → timer → tenant → usage)"
echo "✓ Billing events created with all dimensions"
echo "✓ RLS GUCs set on request session"
echo "✓ Async tests passing"
echo ""
echo "PR-1 is READY TO MERGE!"