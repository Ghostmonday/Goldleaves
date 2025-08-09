# Billing and Plan Limits

This document describes the billing system and plan limits functionality in Goldleaves.

## Plan Types

Goldleaves supports three plan types with different usage limits:

### Free Plan
- **Unit**: `api_calls`
- **Soft Cap**: 500 API calls
- **Hard Cap**: 750 API calls
- **Features**: Basic API access

### Pro Plan
- **Unit**: `api_calls`
- **Soft Cap**: 5,000 API calls
- **Hard Cap**: 7,500 API calls
- **Features**: Enhanced API access with higher limits

### Team Plan
- **Unit**: `api_calls`
- **Soft Cap**: 20,000 API calls
- **Hard Cap**: 30,000 API calls
- **Features**: Team collaboration with highest limits

## Usage Limits Enforcement

### Soft Cap Behavior

When a tenant reaches their soft cap:
- Requests continue to be processed normally
- A response header `X-Plan-SoftCap: true` is added to indicate the soft limit has been reached
- This serves as a warning that the hard cap is approaching

### Hard Cap Behavior

When a tenant reaches their hard cap:
- Further requests are blocked with HTTP status `429 Too Many Requests`
- Response body contains: `{"error": "plan_limit_exceeded"}`
- No further API calls are processed until usage resets or plan is upgraded

## API Endpoints

### GET /billing/summary

Returns current billing and usage information for the authenticated tenant.

**Response Model:**
```json
{
  "unit": "api_calls",
  "soft_cap": 500,
  "hard_cap": 750,
  "remaining": 250,
  "current_usage": 500,
  "plan": "Free"
}
```

**Response Fields:**
- `unit`: The unit of measurement for usage (currently "api_calls")
- `soft_cap`: The soft limit for the current plan
- `hard_cap`: The hard limit for the current plan
- `remaining`: Number of API calls remaining before hard cap (max(hard_cap - current_usage, 0))
- `current_usage`: Current number of API calls used
- `plan`: Current plan name (Free, Pro, or Team)

## Tenant Identification

The system identifies tenants using the following priority order:

1. **Request State**: `request.state.tenant_id` (set by authentication middleware)
2. **Header**: `X-Tenant-ID` header value
3. **Fallback**: Derived from `request.state.user_id` as `tenant_{user_id}`

## Usage Tracking

### Automatic Tracking

The `UsageMiddleware` automatically tracks API usage:
- Increments usage counter for each API request
- Skips tracking for health/docs endpoints: `/health`, `/metrics`, `/docs`, `/openapi.json`, `/auth/*`
- Enforces plan limits before processing requests

### Manual Reset (Development/Testing)

For development and testing purposes, usage can be reset:

```python
from core.entitlements import reset_usage, reset_all_usage

# Reset usage for specific tenant
reset_usage("tenant_id", "api_calls")

# Reset all usage data
reset_all_usage()
```

## Implementation Details

### Plan Configuration

Plan limits are defined in `core/entitlements.py`:

```python
PLAN_LIMITS = {
    "Free": {"unit": "api_calls", "soft": 500, "hard": 750},
    "Pro": {"unit": "api_calls", "soft": 5000, "hard": 7500},
    "Team": {"unit": "api_calls", "soft": 20000, "hard": 30000},
}
```

### Storage

Currently uses in-memory storage for simplicity. In production, this should be replaced with:
- Redis for fast access and persistence
- Database storage for long-term tracking
- Distributed caching for multi-instance deployments

### Middleware Order

The `UsageMiddleware` is positioned after authentication and organization middleware to ensure proper tenant context is available.

## Headers Reference

### Request Headers

- `X-Tenant-ID`: Optional tenant identifier (fallback if not in request state)

### Response Headers

- `X-Plan-SoftCap: true`: Added when soft cap is reached or exceeded (case-insensitive)

## Error Responses

### 429 Too Many Requests

Returned when hard cap is exceeded:

```json
{
  "error": "plan_limit_exceeded"
}
```

### 400 Bad Request

Returned when tenant ID cannot be determined:

```json
{
  "detail": "No tenant ID found in request state or headers"
}
```

## Integration Examples

### Client Implementation

```javascript
// Check billing status
const billingResponse = await fetch('/billing/summary', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'X-Tenant-ID': 'my-tenant-id'
  }
});

const billing = await billingResponse.json();
console.log(`Usage: ${billing.current_usage}/${billing.hard_cap}`);

// Handle soft cap warning
if (response.headers.get('X-Plan-SoftCap') === 'true') {
  console.warn('Approaching plan limit!');
}

// Handle hard cap
if (response.status === 429) {
  const error = await response.json();
  if (error.error === 'plan_limit_exceeded') {
    console.error('Plan limit exceeded - upgrade needed');
  }
}
```

### Monitoring

Monitor the following metrics:
- Usage per tenant and plan type
- Soft cap warnings frequency
- Hard cap blocks frequency
- Plan upgrade conversion rates

## Future Enhancements

Potential improvements for production use:

1. **Multiple Usage Units**: Support for different types of usage (storage, compute, etc.)
2. **Time-based Resets**: Automatic usage reset on billing cycles
3. **Burst Allowance**: Temporary overage allowance
4. **Usage Analytics**: Detailed usage patterns and forecasting
5. **Plan Recommendations**: Automatic suggestions for plan upgrades
6. **Webhook Notifications**: Real-time alerts for limit approaches