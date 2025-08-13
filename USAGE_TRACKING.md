# Usage Event Tags

This implementation adds usage event tracking with feature, jurisdiction, plan, and AI tags to the Goldleaves API.

## Overview

The usage tracking system consists of:

1. **models/usage_event.py** - Database model for storing usage events
2. **core/usage.py** - Core usage tracking functionality
3. **app/usage/middleware.py** - Middleware that reads tags from request.state
4. **Integration** - Added to existing middleware system

## Features

- **Feature tags** with defaults: `feature="unknown"`, `jurisdiction="unknown"`, `plan="unknown"`, `ai=False`
- **Request.state sourcing** - Tags are read from request.state when available
- **No behavior changes** - Existing endpoints are unaffected
- **Optional enablement** - Middleware is available but not auto-enabled

## Usage

### Enabling Usage Tracking

Add to your middleware configuration:

```python
config = {
    "middleware": {
        "usage_tracking": {"enabled": True}
    }
}
```

### Setting Usage Tags

Tags can be set by other middleware or application code:

```python
# In middleware or endpoint handler
request.state.feature = "document_analysis"
request.state.jurisdiction = "us"
request.state.plan = "pro"
request.state.ai = True
```

### Recording Usage Events

Direct usage tracking (optional):

```python
from core.usage import record_usage

# Record with defaults
event_id = await record_usage()

# Record with custom tags
event_id = await record_usage(
    feature="document_analysis",
    jurisdiction="us",
    plan="pro",
    ai=True,
    user_id="user123",
    request_id="req456"
)
```

## Database Schema

The `usage_events` table includes:

- `id` (UUID) - Primary key
- `feature` (str) - Feature being used (default: "unknown")
- `jurisdiction` (str) - Jurisdiction context (default: "unknown")
- `plan` (str) - Plan context (default: "unknown")
- `ai` (bool) - AI feature flag (default: False)
- `event_type` (str) - Type of usage event
- `user_id` (str) - Associated user
- `request_id` (str) - Request correlation ID
- `metadata` (JSON) - Additional event data
- `created_at`, `updated_at` - Timestamps

## Middleware Behavior

The `UsageTrackingMiddleware`:

1. Reads tags from `request.state` with defaults
2. Records usage events for API endpoints (skips health checks, docs)
3. Includes processing time and request metadata
4. Handles errors gracefully without affecting responses

## Default Values

When tags are not set in `request.state`:

- `feature`: "unknown"
- `jurisdiction`: "unknown"
- `plan`: "unknown"
- `ai`: False

## Integration Points

The middleware integrates with existing systems:

- **Authentication middleware** can set user context and plan information
- **Organization middleware** can set jurisdiction and feature context
- **Rate limiting** and **audit** middleware work alongside usage tracking
- **Request context** middleware provides request IDs and timing

## Testing

Run validation tests:

```bash
python validate_implementation.py
python demonstrate_usage.py
```

## Configuration Examples

### Development (not auto-enabled)
```python
# Usage tracking available but not explicitly enabled
config = {
    "middleware": {
        "rate_limit": {"enabled": True},
        "security": {"enabled": True},
        "audit": {"enabled": True}
        # usage_tracking not listed = available but not explicitly enabled
    }
}
```

### Production (explicitly enabled)
```python
config = {
    "middleware": {
        "rate_limit": {"enabled": True},
        "security": {"enabled": True},
        "audit": {"enabled": True},
        "usage_tracking": {"enabled": True}  # Explicitly enabled
    }
}
```

### Disabled
```python
config = {
    "middleware": {
        "usage_tracking": {"enabled": False}  # Explicitly disabled
    }
}
```

## Constraints Followed

- ✅ **Minimal implementation** - Self-contained components
- ✅ **No auto-enablement** - Middleware available but not enabled by default
- ✅ **No behavior changes** - Existing endpoints unaffected
- ✅ **Default values** - All fields have sensible defaults
- ✅ **Request.state sourcing** - Tags read from request state when available
