# Usage Live Wire Implementation

This implementation replaces mock usage data with live metering endpoints and wires the frontend to consume them with graceful fallback.

## Backend API

### Endpoints

#### GET /api/v1/usage/summary
Returns current billing period usage summary:
```json
{
  "total_calls": 1250,
  "est_cost_cents": 2500,
  "window_start": "2024-01-01T00:00:00Z",
  "window_end": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/usage/daily?days=7
Returns daily usage for specified number of days (1-90):
```json
{
  "usage": [
    {"date": "2024-01-08", "calls": 180},
    {"date": "2024-01-09", "calls": 195},
    {"date": "2024-01-10", "calls": 165}
  ]
}
```

### Authentication
Both endpoints require authentication and are scoped by tenant_id/user_id from context.

## Frontend Integration

### Environment Variables

Add to your `.env` file:
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_USE_LIVE_USAGE=1
NEXT_PUBLIC_USAGE_RATE_CENTS=2
```

### Usage Hook

```typescript
import { useUsage } from './usage';

function UsageComponent() {
  const { summary, dailyUsage, loading, error, refetch } = useUsage(7);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Total Calls: {summary?.total_calls}</h2>
      <h3>Estimated Cost: ${summary?.est_cost_cents / 100}</h3>
      {/* Chart component using dailyUsage */}
    </div>
  );
}
```

### Graceful Fallback

The frontend automatically falls back to mock data when:
- `USE_LIVE_USAGE` is not set to "1"
- API requests fail
- Authentication errors occur

## Testing

### Backend Tests
```bash
cd /path/to/project
python -m pytest tests/usage/test_api.py -v
```

### Test Coverage
- Authentication required for all endpoints
- Parameter validation (days 1-90)
- Response schema validation
- Error handling
- Mock data consistency

## File Structure

```
routers/
├── usage.py              # Usage endpoints
├── contract.py           # Router registration
└── dependencies.py       # Auth dependencies

apps/web/src/usage/
├── useUsage.ts           # React hook with live data
├── UsagePage.tsx         # Demo usage page
├── UsagePage.css         # Styles
└── index.ts              # Module exports

tests/usage/
├── __init__.py
└── test_api.py           # API endpoint tests
```

## Implementation Notes

- Router is automatically registered via contract system
- Mock implementation with proper structure for production replacement
- UTC timestamps throughout
- Cost calculation from configurable rate
- Request ID ignored as specified
- Additive changes only - no breaking modifications
