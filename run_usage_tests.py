#!/usr/bin/env python3
"""Standalone test runner for usage latency tests."""

import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test functions
from tests.usage.test_latency import (
    create_test_app,
    test_successful_request_tracking,
    test_error_request_tracking,
    test_multiple_requests,
    test_latency_measurement,
    test_request_id_from_header,
    test_reset_events_functionality
)
from fastapi.testclient import TestClient

def run_tests():
    """Run all usage latency tests."""
    import core.usage
    
    app = create_test_app()
    test_client = TestClient(app)
    
    tests = [
        ("test_successful_request_tracking", lambda: test_successful_request_tracking(test_client)),
        ("test_error_request_tracking", lambda: test_error_request_tracking(test_client)),
        ("test_multiple_requests", lambda: test_multiple_requests(test_client)),
        ("test_latency_measurement", lambda: test_latency_measurement(test_client)),
        ("test_request_id_from_header", lambda: test_request_id_from_header(test_client)),
        ("test_reset_events_functionality", test_reset_events_functionality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            # Reset events before each test
            core.usage.reset_events()
            test_func()
            print(f"✓ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)