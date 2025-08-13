"""Tests for usage event latency tracking."""

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.usage.middleware import UsageMiddleware
import core.usage


def create_test_app() -> FastAPI:
    """Create a small FastAPI test app with UsageMiddleware."""
    app = FastAPI()

    # Add the UsageMiddleware
    app.add_middleware(UsageMiddleware)

    # Define test routes
    @app.get("/ok")
    async def ok_endpoint():
        """Returns success response."""
        return {"ok": True}

    @app.get("/bad")
    async def bad_endpoint():
        """Returns error response."""
        return JSONResponse(status_code=400, content={"error": "Bad request"})

    return app


@pytest.fixture
def test_client():
    """Create test client with the test app."""
    app = create_test_app()
    return TestClient(app)


def test_successful_request_tracking(test_client):
    """Test that successful requests are tracked correctly."""
    # Reset events before test
    core.usage.reset_events()

    # Make request to /ok endpoint
    response = test_client.get("/ok")

    # Verify response is unchanged
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # Verify one event was recorded
    events = core.usage.get_events()
    assert len(events) == 1

    event = events[0]
    assert event["status_code"] == 200
    assert event["result"] == "success"
    assert event["latency_ms"] >= 0  # Allow 0 for very fast operations
    assert "request_id" in event


def test_error_request_tracking(test_client):
    """Test that error requests are tracked correctly."""
    # Reset events before test
    core.usage.reset_events()

    # Make request to /bad endpoint
    response = test_client.get("/bad")

    # Verify response is unchanged
    assert response.status_code == 400
    assert response.json() == {"error": "Bad request"}

    # Verify one event was recorded
    events = core.usage.get_events()
    assert len(events) == 1

    event = events[0]
    assert event["status_code"] == 400
    assert event["result"] == "error"
    assert event["latency_ms"] >= 0  # Allow 0 for very fast operations
    assert "request_id" in event


def test_multiple_requests(test_client):
    """Test that multiple requests are tracked separately."""
    # Reset events before test
    core.usage.reset_events()

    # Make multiple requests
    response1 = test_client.get("/ok")
    response2 = test_client.get("/bad")
    response3 = test_client.get("/ok")

    # Verify responses are unchanged
    assert response1.status_code == 200
    assert response2.status_code == 400
    assert response3.status_code == 200

    # Verify three events were recorded
    events = core.usage.get_events()
    assert len(events) == 3

    # Verify event details
    assert events[0]["status_code"] == 200
    assert events[0]["result"] == "success"

    assert events[1]["status_code"] == 400
    assert events[1]["result"] == "error"

    assert events[2]["status_code"] == 200
    assert events[2]["result"] == "success"

    # Verify all events have different request_ids
    request_ids = [event["request_id"] for event in events]
    assert len(set(request_ids)) == 3  # All unique


def test_latency_measurement(test_client):
    """Test that latency is measured and is reasonable."""
    # Reset events before test
    core.usage.reset_events()

    # Make request
    response = test_client.get("/ok")
    assert response.status_code == 200

    # Get recorded event
    events = core.usage.get_events()
    assert len(events) == 1

    event = events[0]
    latency_ms = event["latency_ms"]

    # Latency should be non-negative and reasonable (less than 1000ms for simple endpoint)
    assert latency_ms >= 0  # Allow 0 for very fast operations
    assert latency_ms < 1000


def test_request_id_from_header(test_client):
    """Test that request ID is extracted from X-Request-ID header."""
    # Reset events before test
    core.usage.reset_events()

    # Make request with custom request ID header
    custom_request_id = "test-request-123"
    response = test_client.get("/ok", headers={"X-Request-ID": custom_request_id})

    assert response.status_code == 200

    # Verify the custom request ID was used
    events = core.usage.get_events()
    assert len(events) == 1
    assert events[0]["request_id"] == custom_request_id


def test_reset_events_functionality():
    """Test that reset_events() clears all recorded events."""
    # Add some events first
    core.usage.record_usage("test-1", 200, 100)
    core.usage.record_usage("test-2", 404, 150)

    # Verify events exist
    events = core.usage.get_events()
    assert len(events) == 2

    # Reset events
    core.usage.reset_events()

    # Verify events are cleared
    events = core.usage.get_events()
    assert len(events) == 0
