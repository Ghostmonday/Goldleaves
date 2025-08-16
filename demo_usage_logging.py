#!/usr/bin/env python3
"""
Demo script showing usage logging functionality.
Demonstrates the key features without requiring database setup.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any

class MockRequest:
    """Mock request object for demonstration."""
    def __init__(self, method: str, path: str, headers: Dict[str, str] = None):
        self.method = method
        self.url = MockURL(path)
        self.headers = headers or {}
        self.state = MockState()
        self.query_params = {}

class MockURL:
    """Mock URL object."""
    def __init__(self, path: str):
        self.path = path

class MockState:
    """Mock request state."""
    def __init__(self):
        pass

class MockResponse:
    """Mock response object."""
    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers = {}

def demo_request_id_generation():
    """Demonstrate request ID generation and ensuring."""
    print("🔍 Demo: Request ID Generation")
    print("-" * 40)

    # Simulate middleware ensuring request ID
    request1 = MockRequest("GET", "/api/v1/documents")
    request_id1 = request1.headers.get('X-Request-ID')

    if not request_id1:
        request_id1 = str(uuid.uuid4())
        request1.state.request_id = request_id1
        print(f"✅ Generated request ID: {request_id1}")

    # Simulate request with existing ID
    existing_id = str(uuid.uuid4())
    request2 = MockRequest("POST", "/api/v1/documents", {"X-Request-ID": existing_id})
    request_id2 = request2.headers.get('X-Request-ID')
    print(f"✅ Using existing request ID: {request_id2}")

    print()

def demo_billable_route_detection():
    """Demonstrate billable route detection."""
    print("🔍 Demo: Billable Route Detection")
    print("-" * 40)

    # Mock environment variable
    billable_routes = ['/api/v1/documents', '/api/v1/cases', '/api/v1/clients']

    test_routes = [
        '/api/v1/documents',      # Billable
        '/api/v1/documents/123',  # Billable (starts with pattern)
        '/api/v1/cases/create',   # Billable
        '/health',                # Not billable
        '/docs',                  # Not billable
        '/api/v1/users'           # Not billable
    ]

    for route in test_routes:
        is_billable = any(route.startswith(pattern) for pattern in billable_routes)
        status = "💰 BILLABLE" if is_billable else "🆓 FREE"
        print(f"  {route:<25} -> {status}")

    print()

def demo_tenant_extraction():
    """Demonstrate tenant ID extraction from various sources."""
    print("🔍 Demo: Tenant ID Extraction")
    print("-" * 40)

    # Priority 1: From request state (organization middleware)
    request1 = MockRequest("GET", "/api/v1/documents")
    request1.state.organization_id = "org_from_state"
    request1.headers["X-Organization-ID"] = "org_from_header"

    # Simulate middleware logic
    tenant_id = getattr(request1.state, 'organization_id', None)
    if not tenant_id:
        tenant_id = request1.headers.get('X-Organization-ID')
    print(f"✅ Tenant from state: {tenant_id}")

    # Priority 2: From header only
    request2 = MockRequest("GET", "/api/v1/documents")
    request2.headers["X-Organization-ID"] = "org_from_header_only"

    tenant_id2 = getattr(request2.state, 'organization_id', None)
    if not tenant_id2:
        tenant_id2 = request2.headers.get('X-Organization-ID')
    print(f"✅ Tenant from header: {tenant_id2}")

    # Priority 3: Fallback to user ID
    request3 = MockRequest("GET", "/api/v1/documents")
    request3.state.user_id = "user_123"

    tenant_id3 = getattr(request3.state, 'organization_id', None)
    if not tenant_id3:
        tenant_id3 = request3.headers.get('X-Organization-ID')
    if not tenant_id3:
        user_id = getattr(request3.state, 'user_id', None)
        if user_id:
            tenant_id3 = f"user_{user_id}"
    print(f"✅ Tenant from user fallback: {tenant_id3}")

    print()

def demo_usage_event_creation():
    """Demonstrate usage event creation with idempotency."""
    print("🔍 Demo: Usage Event Creation")
    print("-" * 40)

    # Simulate creating a usage event
    request_id = str(uuid.uuid4())
    usage_event_data = {
        'id': str(uuid.uuid4()),
        'request_id': request_id,
        'tenant_id': 'org_123',
        'user_id': 'user_456',
        'route': '/api/v1/documents',
        'action': 'create',
        'units': 1.0,
        'cost_cents': 25,
        'ts': datetime.utcnow().isoformat(),
        'metadata': json.dumps({
            'method': 'POST',
            'status_code': 201,
            'user_agent': 'Goldleaves/1.0',
            'client_ip': '192.168.1.100'
        })
    }

    print("✅ Usage event created:")
    for key, value in usage_event_data.items():
        if key == 'metadata':
            value = json.loads(value)
        print(f"  {key:<15}: {value}")

    # Simulate idempotency - same request_id
    print(f"\n🔄 Attempting to create duplicate with same request_id...")
    print(f"✅ Idempotency check: Would return existing event (no duplicate)")

    print()

def demo_middleware_flow():
    """Demonstrate complete middleware flow."""
    print("🔍 Demo: Complete Middleware Flow")
    print("-" * 40)

    # Simulate authenticated request to billable endpoint
    request = MockRequest("POST", "/api/v1/documents")
    request.headers["Authorization"] = "Bearer eyJ..."
    request.state.user_id = "user_789"
    request.state.organization_id = "org_456"

    response = MockResponse(201)

    print("📝 Request details:")
    print(f"  Method: {request.method}")
    print(f"  Route: {request.url.path}")
    print(f"  User ID: {getattr(request.state, 'user_id', 'None')}")
    print(f"  Tenant ID: {getattr(request.state, 'organization_id', 'None')}")

    # Check if billable
    billable_routes = ['/api/v1/documents', '/api/v1/cases']
    is_billable = any(request.url.path.startswith(route) for route in billable_routes)

    print(f"\n🔍 Processing:")
    print(f"  Is billable route: {is_billable}")
    print(f"  Has user context: {hasattr(request.state, 'user_id')}")
    print(f"  Response status: {response.status_code}")

    if is_billable and hasattr(request.state, 'user_id') and response.status_code < 400:
        request_id = str(uuid.uuid4())
        print(f"\n✅ Would create usage event:")
        print(f"  Request ID: {request_id}")
        print(f"  Tenant: {getattr(request.state, 'organization_id')}")
        print(f"  User: {getattr(request.state, 'user_id')}")
        print(f"  Route: {request.url.path}")
        print(f"  Action: create")
        print(f"  Units: 1.0")
        print(f"  Estimated cost: 25 cents")
    else:
        print(f"\n❌ Would NOT create usage event")

    print()

def demo_auth_failure_skip():
    """Demonstrate skipping usage tracking on auth failures."""
    print("🔍 Demo: Auth Failure Skip")
    print("-" * 40)

    # Simulate 401 Unauthorized response
    request = MockRequest("GET", "/api/v1/documents")
    response = MockResponse(401)

    print("📝 Request details:")
    print(f"  Route: {request.url.path}")
    print(f"  Response status: {response.status_code}")

    if 400 <= response.status_code < 500:
        print("✅ Skipping usage tracking due to 4xx auth failure")
    else:
        print("✅ Would track usage (success response)")

    print()

def demo_cost_calculation():
    """Demonstrate cost calculation."""
    print("🔍 Demo: Cost Calculation")
    print("-" * 40)

    rate_cents = 25  # From USAGE_RATE_CENTS env var

    test_cases = [
        (1.0, "Single document request"),
        (2.5, "Bulk operation (2.5 units)"),
        (0.1, "Small API call"),
        (10.0, "Large processing job")
    ]

    for units, description in test_cases:
        cost_cents = int(units * rate_cents)
        cost_dollars = cost_cents / 100
        print(f"  {units:>5} units x {rate_cents} cents = {cost_cents:>3} cents (${cost_dollars:.2f}) - {description}")

    print()

def demo_usage_summary():
    """Demonstrate usage summary generation."""
    print("🔍 Demo: Usage Summary")
    print("-" * 40)

    # Mock usage data for a tenant
    mock_events = [
        {'route': '/api/v1/documents', 'units': 5.0, 'cost_cents': 125},
        {'route': '/api/v1/cases', 'units': 2.0, 'cost_cents': 50},
        {'route': '/api/v1/clients', 'units': 1.0, 'cost_cents': 25},
        {'route': '/api/v1/documents', 'units': 3.0, 'cost_cents': 75},
    ]

    # Calculate summary
    total_events = len(mock_events)
    total_units = sum(event['units'] for event in mock_events)
    total_cost_cents = sum(event['cost_cents'] for event in mock_events)
    unique_routes = len(set(event['route'] for event in mock_events))

    print("📊 Usage Summary for tenant 'org_123':")
    print(f"  Period: 2024-01-01 to 2024-01-31")
    print(f"  Total events: {total_events}")
    print(f"  Total units: {total_units}")
    print(f"  Total cost: {total_cost_cents} cents (${total_cost_cents/100:.2f})")
    print(f"  Unique routes: {unique_routes}")

    # Route breakdown
    route_summary = {}
    for event in mock_events:
        route = event['route']
        if route not in route_summary:
            route_summary[route] = {'count': 0, 'units': 0, 'cost_cents': 0}
        route_summary[route]['count'] += 1
        route_summary[route]['units'] += event['units']
        route_summary[route]['cost_cents'] += event['cost_cents']

    print("\n📈 Route breakdown:")
    for route, data in route_summary.items():
        print(f"  {route}:")
        print(f"    Events: {data['count']}")
        print(f"    Units: {data['units']}")
        print(f"    Cost: {data['cost_cents']} cents")

    print()

def main():
    """Run all demos."""
    print("🚀 Usage Logging Implementation Demo")
    print("=" * 60)
    print("This demo shows how the usage logging system works")
    print("without requiring database setup or external dependencies.")
    print("=" * 60)
    print()

    demos = [
        demo_request_id_generation,
        demo_billable_route_detection,
        demo_tenant_extraction,
        demo_usage_event_creation,
        demo_middleware_flow,
        demo_auth_failure_skip,
        demo_cost_calculation,
        demo_usage_summary
    ]

    for demo in demos:
        demo()

    print("=" * 60)
    print("🎉 Demo completed! Key features demonstrated:")
    print("  ✅ Request ID generation and idempotency")
    print("  ✅ Billable route detection")
    print("  ✅ Multi-source tenant ID extraction")
    print("  ✅ Usage event creation with metadata")
    print("  ✅ Complete middleware processing flow")
    print("  ✅ Auth failure handling")
    print("  ✅ Cost calculation")
    print("  ✅ Usage reporting and analytics")
    print()
    print("💡 The actual implementation includes:")
    print("  • SQLAlchemy database integration")
    print("  • Async processing for performance")
    print("  • Comprehensive error handling")
    print("  • FastAPI middleware integration")
    print("  • Stripe billing API stubs")

if __name__ == "__main__":
    main()
