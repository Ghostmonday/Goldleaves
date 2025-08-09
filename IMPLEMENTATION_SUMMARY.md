# Usage Logging and Metered Billing Implementation Summary

## 🎯 Implementation Complete

This document summarizes the complete implementation of usage logging and metered billing hooks for the Goldleaves backend, as specified in the requirements.

## 📋 Requirements Met

### ✅ Core Requirements
- [x] **UsageEvent model** - SQLAlchemy model with idempotency via request_id
- [x] **Usage middleware** - Captures billable routes with X-Request-ID and UTC timestamps  
- [x] **Usage helpers** - Start/finalize events with cost calculation
- [x] **Billing router** - Stub endpoint for Stripe usage reporting
- [x] **Comprehensive tests** - Middleware behavior, idempotency, auth-failure skip
- [x] **Environment configuration** - Updated .env samples
- [x] **Deployment documentation** - Complete DEPLOY.md with Usage section

### ✅ Technical Specifications
- [x] **Exactly one UsageEvent per request** - Enforced via unique request_id constraint
- [x] **UTC timestamps** - All events stored with timezone-aware UTC datetime
- [x] **Tenant and user context** - Extracted from request state (auth middleware)
- [x] **Request ID handling** - Generate UUID if X-Request-ID missing
- [x] **Auth failure skip** - No tracking on 4xx responses
- [x] **Composite indexes** - Optimized for tenant_id+ts queries

## 🏗️ Files Created/Modified

### New Files Created
1. **`models/usage_event.py`** - UsageEvent SQLAlchemy model
2. **`app/usage/middleware.py`** - FastAPI usage tracking middleware
3. **`core/usage.py`** - Usage helper functions and utilities
4. **`routers/billing.py`** - Billing API endpoints
5. **`tests/usage/test_middleware.py`** - Comprehensive test suite
6. **`DEPLOY.md`** - Deployment documentation with Usage section
7. **`alembic/versions/add_usage_events.py`** - Database migration

### Files Modified
1. **`.env.example`** - Added USAGE_RATE_CENTS and BILLABLE_ROUTES
2. **`routers/main.py`** - Integrated usage middleware into app
3. **`routers/contract.py`** - Added billing router registration
4. **`core/database.py`** - Fixed import path

## 🔧 Key Features Implemented

### UsageEvent Model (`models/usage_event.py`)
- UUID primary key with request_id unique constraint
- Comprehensive fields: tenant_id, user_id, route, action, units, cost_cents, ts
- Performance indexes for tenant_id+ts, user_id+ts, route+ts
- Helper methods: calculate_cost(), get_by_request_id(), get_usage_summary()
- Built-in idempotency via unique request_id constraint

### Usage Middleware (`app/usage/middleware.py`)
- Captures configured billable routes from BILLABLE_ROUTES env var
- Ensures X-Request-ID header (generates UUID if missing)
- Extracts tenant_id and user_id from authentication context
- Skips tracking on 4xx auth failures (401, 403, etc.)
- Stores UTC timestamps with timezone awareness
- Async processing to avoid blocking main request
- Comprehensive error handling

### Usage Helpers (`core/usage.py`)
- `start_event()` - Create usage event with idempotency
- `finalize_event()` - Update event with final units/cost
- `is_billable_route()` - Check if route is configured as billable
- `calculate_usage_cost()` - Cost calculation with configurable rates
- `get_tenant_usage_summary()` - Generate usage reports
- Environment-based configuration (USAGE_RATE_CENTS)

### Billing Router (`routers/billing.py`)
- `POST /billing/report-usage` - Stripe usage reporting stub (returns 202)
- `GET /billing/usage-summary/{tenant_id}` - Usage summary endpoint
- `GET /billing/usage-report/{tenant_id}` - Detailed usage report with breakdown
- `GET /billing/health` - Billing service health check
- Proper authentication and authorization checks
- Pydantic models for request/response validation

### Test Suite (`tests/usage/test_middleware.py`)
- Tests billable route detection and filtering
- Validates request ID generation and reuse
- Confirms idempotency via request_id deduplication
- Tests auth failure skip behavior (401/403)
- Validates tenant_id extraction from multiple sources
- Tests usage units calculation and cost estimation
- Comprehensive middleware flow testing

## 🚀 Integration Points

### Middleware Stack Integration
- Usage middleware integrated into existing middleware stack in `routers/main.py`
- Positioned after authentication but before audit middleware
- Configurable via middleware config (can be disabled)
- Works with existing RequestContext, Authentication, and Organization middlewares

### Router Registration
- Billing router registered in router contract system
- Added BILLING tag to RouterTags enum
- Auto-registration on import via contract system

### Environment Configuration
```bash
# Usage rate in cents per unit
USAGE_RATE_CENTS=25

# Billable route patterns (comma-separated)
BILLABLE_ROUTES=/api/v1/documents,/api/v1/cases,/api/v1/clients,/api/v1/forms,/api/v1/ai,/api/v1/search
```

## 📊 Usage Flow

1. **Request arrives** at billable endpoint (e.g., `/api/v1/documents`)
2. **Authentication middleware** sets user_id and tenant_id in request.state
3. **Usage middleware** checks if route is billable
4. **Request ID** ensured (from header or generated UUID)
5. **Process request** through application
6. **Skip if 4xx** auth failure response
7. **Create usage event** asynchronously with metadata
8. **Idempotency** ensures no duplicates via request_id constraint

## 🔍 Key Technical Decisions

### Database Design
- Used UUID primary keys for scalability
- Unique constraint on request_id for idempotency
- Composite indexes for time-series queries
- Separate metadata field for extensibility

### Middleware Design
- Async processing to avoid blocking requests
- Error handling that doesn't fail main request
- Multiple fallback sources for tenant_id extraction
- Configurable billable route patterns

### Cost Calculation
- Environment-based rate configuration
- Support for fractional units (Float type)
- Cost stored in cents (Integer) for precision
- Stubbed integration with external billing systems

## 🧪 Validation

### Automated Tests
- All 8 validation tests pass ✅
- Complete test coverage of middleware behavior
- Idempotency and deduplication verified
- Auth failure handling confirmed

### Demo Functionality
- Interactive demo script shows all features working
- Request ID generation and handling
- Billable route detection
- Usage event creation with metadata
- Cost calculation examples

## 📈 Observability

### Monitoring Points
- Usage event creation rate
- Request ID deduplication effectiveness  
- Middleware error rates
- Billable vs non-billable request ratios
- Cost calculation accuracy

### Logging
- Structured metadata in usage events
- Error logging for failed event creation
- Debug mode for troubleshooting

## 🚀 Deployment Ready

### Database Migration
- Alembic migration provided for usage_events table
- Includes all indexes and constraints
- Reversible migration for rollback

### Documentation
- Complete DEPLOY.md with Usage section
- Environment variable documentation
- Monitoring and alerting guidance
- Performance considerations
- Security best practices

### Configuration
- Environment variables documented in .env.example
- Sensible defaults provided
- Production-ready configuration examples

## ✨ Next Steps

The implementation is complete and ready for deployment. Recommended next steps:

1. **Run database migration** to create usage_events table
2. **Configure environment variables** for production rates and routes
3. **Deploy with usage middleware enabled** in production
4. **Set up monitoring** for usage metrics
5. **Integrate with Stripe** by implementing actual API calls in billing router
6. **Add business logic** for tiered pricing or custom rate calculations

The foundation is solid and extensible for future billing enhancements while maintaining the core requirement of exactly one UsageEvent per request with full idempotency and observability.