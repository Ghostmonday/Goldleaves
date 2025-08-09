# Goldleaves Backend Deployment Guide

## Overview

This guide covers the deployment configuration for the Goldleaves backend API, including the new usage tracking and metered billing features.

## Environment Variables

### Core Configuration

```bash
# Application Environment
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Authentication
JWT_SECRET=your-secure-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# CORS
ALLOWED_ORIGINS=https://app.goldleaves.com,https://admin.goldleaves.com
```

### Usage Tracking & Metered Billing

The backend includes comprehensive usage tracking and metered billing capabilities:

#### Environment Variables

```bash
# Usage rate in cents per unit (default: 25 cents)
USAGE_RATE_CENTS=25

# Billable routes (comma-separated patterns)
BILLABLE_ROUTES=/api/v1/documents,/api/v1/cases,/api/v1/clients,/api/v1/forms,/api/v1/ai,/api/v1/search
```

#### How Usage Tracking Works

1. **Middleware Integration**: The `UsageTrackingMiddleware` automatically captures requests to configured billable routes
2. **Request Identification**: Each request gets a unique X-Request-ID (generated if missing)
3. **Idempotency**: Duplicate requests with the same request_id create only one usage event
4. **Context Extraction**: User and tenant information is extracted from authentication middleware
5. **UTC Timestamps**: All usage events are stored with timezone-aware UTC timestamps

#### Billable Route Configuration

Routes matching patterns in `BILLABLE_ROUTES` will be tracked:

- `/api/v1/documents` - Document operations
- `/api/v1/cases` - Case management  
- `/api/v1/clients` - Client management
- `/api/v1/forms` - Form operations
- `/api/v1/ai` - AI-powered features
- `/api/v1/search` - Search operations

Routes automatically excluded from billing:
- `/health` - Health checks
- `/docs` - API documentation
- `/auth/*` - Authentication endpoints
- `/metrics` - Monitoring endpoints

#### Database Schema

The usage tracking system creates a `usage_events` table with:

```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    route VARCHAR(500) NOT NULL,
    action VARCHAR(255) NOT NULL,
    units FLOAT NOT NULL DEFAULT 1.0,
    cost_cents INTEGER,
    ts TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata VARCHAR(2000),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Performance indexes
CREATE INDEX idx_usage_tenant_ts ON usage_events(tenant_id, ts);
CREATE INDEX idx_usage_user_ts ON usage_events(user_id, ts);
CREATE INDEX idx_usage_route_ts ON usage_events(route, ts);
```

#### Middleware Integration

To enable usage tracking, add the middleware to your FastAPI application:

```python
from app.usage.middleware import UsageTrackingMiddleware

app = FastAPI()
app.add_middleware(UsageTrackingMiddleware)
```

**Important**: The usage middleware should be added after authentication middleware to ensure user context is available.

#### Billing API Endpoints

The billing router provides endpoints for usage reporting:

- `POST /billing/report-usage` - Report usage to external billing systems (Stripe)
- `GET /billing/usage-summary/{tenant_id}` - Get usage summary for a tenant
- `GET /billing/usage-report/{tenant_id}` - Get detailed usage report with route breakdown
- `GET /billing/health` - Billing service health check

#### Observability

##### Monitoring Usage Events

Monitor usage event creation:

```bash
# Count usage events by tenant
SELECT tenant_id, COUNT(*) as event_count 
FROM usage_events 
WHERE ts >= NOW() - INTERVAL '24 hours'
GROUP BY tenant_id;

# Monitor billable route usage
SELECT route, COUNT(*) as requests, SUM(units) as total_units
FROM usage_events 
WHERE ts >= NOW() - INTERVAL '7 days'
GROUP BY route;
```

##### Key Metrics to Track

1. **Usage Event Creation Rate**: Events per minute/hour
2. **Request ID Deduplication**: Percentage of duplicate request_ids
3. **Middleware Errors**: Failed usage event creations
4. **Billable vs Non-billable Requests**: Request distribution
5. **Cost Calculation**: Revenue per tenant/time period

##### Logging

Usage events include structured metadata:

```json
{
  "method": "POST",
  "status_code": 201,
  "user_agent": "...",
  "client_ip": "192.168.1.1",
  "response_size": "1024",
  "processing_time": 0.15
}
```

##### Alerting

Set up alerts for:

- High usage event creation failures
- Unusual billing patterns
- Missing request context (user_id/tenant_id)
- Database connection issues for usage tracking

#### Security Considerations

1. **Authentication Required**: Usage tracking only occurs for authenticated requests
2. **Tenant Isolation**: Users can only access their tenant's usage data
3. **Rate Limiting**: Usage tracking respects existing rate limits
4. **Data Privacy**: Usage events contain only necessary billing metadata

#### Performance Impact

The usage tracking middleware is designed for minimal performance impact:

- **Async Operations**: Usage events are created asynchronously
- **Database Optimizations**: Indexes optimized for time-series queries
- **Error Handling**: Failures don't affect main request processing
- **Idempotency**: Duplicate detection prevents unnecessary database writes

#### Backup and Retention

Usage events are critical for billing accuracy:

- **Backup**: Include `usage_events` table in regular database backups
- **Retention**: Consider data retention policies based on billing requirements
- **Archival**: Implement archival strategy for old usage data

## Database Migration

Run Alembic migrations to create usage tracking tables:

```bash
alembic upgrade head
```

## Health Checks

Verify deployment health:

```bash
# Application health
curl https://api.goldleaves.com/health

# Billing service health  
curl https://api.goldleaves.com/billing/health

# Usage tracking test (authenticated)
curl -H "Authorization: Bearer <token>" \
     -H "X-Organization-ID: org_123" \
     https://api.goldleaves.com/api/v1/documents
```

## Troubleshooting

### Common Issues

1. **Usage Events Not Created**
   - Verify `BILLABLE_ROUTES` configuration
   - Check authentication middleware is running before usage middleware
   - Ensure database connectivity

2. **Missing Request Context**
   - Verify authentication middleware provides `user_id` in request state
   - Check organization middleware sets `organization_id`

3. **Duplicate Usage Events**
   - Should not happen due to request_id uniqueness constraint
   - Check for request_id generation issues

### Debug Mode

Enable debug logging to troubleshoot usage tracking:

```bash
LOG_LEVEL=DEBUG
```

This will log usage event creation attempts and errors.

## Production Checklist

- [ ] Configure `USAGE_RATE_CENTS` for production billing
- [ ] Set `BILLABLE_ROUTES` to match your API structure  
- [ ] Ensure database has usage_events table and indexes
- [ ] Verify authentication middleware integration
- [ ] Set up monitoring for usage metrics
- [ ] Configure backup strategy including usage data
- [ ] Test billing API endpoints
- [ ] Validate request ID generation and deduplication
- [ ] Set up alerting for usage tracking failures