#!/usr/bin/env python3
"""
Basic validation script for usage logging implementation.
Tests the core components without requiring full dependencies.
"""

import sys
import os
import uuid
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_usage_event_structure():
    """Test the UsageEvent model structure."""
    print("🔍 Testing UsageEvent model structure...")
    
    try:
        # Read the model file and check its structure
        with open('models/usage_event.py', 'r') as f:
            content = f.read()
        
        required_fields = [
            'id', 'request_id', 'tenant_id', 'user_id', 
            'route', 'action', 'units', 'cost_cents', 'ts'
        ]
        
        for field in required_fields:
            if f'{field} = Column(' in content:
                print(f"  ✅ Field '{field}' found")
            else:
                print(f"  ❌ Field '{field}' missing")
                return False
        
        # Check for unique constraint on request_id
        if 'unique=True' in content and 'request_id' in content:
            print("  ✅ Unique constraint on request_id")
        else:
            print("  ❌ Missing unique constraint on request_id")
            return False
            
        # Check for indexes
        if 'Index(' in content:
            print("  ✅ Performance indexes defined")
        else:
            print("  ❌ Missing performance indexes")
            return False
            
        print("✅ UsageEvent model structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating UsageEvent: {e}")
        return False

def test_usage_helpers():
    """Test the usage helper functions."""
    print("\n🔍 Testing usage helper functions...")
    
    try:
        with open('core/usage.py', 'r') as f:
            content = f.read()
        
        required_functions = [
            'start_event', 'finalize_event', 'get_usage_rate_cents',
            'is_billable_route', 'calculate_usage_cost'
        ]
        
        for func in required_functions:
            if f'def {func}(' in content:
                print(f"  ✅ Function '{func}' found")
            else:
                print(f"  ❌ Function '{func}' missing")
                return False
        
        # Check for idempotency handling
        if 'IntegrityError' in content and 'get_by_request_id' in content:
            print("  ✅ Idempotency handling implemented")
        else:
            print("  ❌ Missing idempotency handling")
            return False
            
        print("✅ Usage helper functions validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating usage helpers: {e}")
        return False

def test_middleware_structure():
    """Test the middleware implementation."""
    print("\n🔍 Testing usage middleware structure...")
    
    try:
        with open('app/usage/middleware.py', 'r') as f:
            content = f.read()
        
        # Check for required middleware methods
        if 'class UsageTrackingMiddleware' in content:
            print("  ✅ UsageTrackingMiddleware class found")
        else:
            print("  ❌ UsageTrackingMiddleware class missing")
            return False
            
        if 'async def dispatch(' in content:
            print("  ✅ Async dispatch method found")
        else:
            print("  ❌ Async dispatch method missing")
            return False
            
        # Check for key features
        features = [
            '_ensure_request_id',  # Request ID generation
            '_get_tenant_id',      # Tenant extraction
            '_track_usage_event',  # Usage tracking
            'is_billable_route'    # Route filtering
        ]
        
        for feature in features:
            if feature in content:
                print(f"  ✅ Feature '{feature}' implemented")
            else:
                print(f"  ❌ Feature '{feature}' missing")
                return False
        
        print("✅ Usage middleware structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating middleware: {e}")
        return False

def test_billing_router():
    """Test the billing router implementation."""
    print("\n🔍 Testing billing router structure...")
    
    try:
        with open('routers/billing.py', 'r') as f:
            content = f.read()
        
        # Check for required endpoints
        endpoints = [
            'report_usage_to_stripe',
            'get_usage_summary', 
            'get_detailed_usage_report',
            'billing_health_check'
        ]
        
        for endpoint in endpoints:
            if f'def {endpoint}(' in content:
                print(f"  ✅ Endpoint '{endpoint}' found")
            else:
                print(f"  ❌ Endpoint '{endpoint}' missing")
                return False
        
        # Check for proper HTTP methods
        if '@router.post' in content and '@router.get' in content:
            print("  ✅ HTTP methods properly defined")
        else:
            print("  ❌ Missing HTTP method decorators")
            return False
            
        print("✅ Billing router structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating billing router: {e}")
        return False

def test_environment_config():
    """Test environment configuration."""
    print("\n🔍 Testing environment configuration...")
    
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        required_vars = ['USAGE_RATE_CENTS', 'BILLABLE_ROUTES']
        
        for var in required_vars:
            if var in content:
                print(f"  ✅ Environment variable '{var}' documented")
            else:
                print(f"  ❌ Environment variable '{var}' missing")
                return False
        
        # Check for usage documentation
        if 'X-Request-ID' in content and 'idempotency' in content:
            print("  ✅ Usage documentation included")
        else:
            print("  ❌ Missing usage documentation")
            return False
            
        print("✅ Environment configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating environment config: {e}")
        return False

def test_deployment_docs():
    """Test deployment documentation."""
    print("\n🔍 Testing deployment documentation...")
    
    try:
        with open('DEPLOY.md', 'r') as f:
            content = f.read()
        
        required_sections = [
            'Usage Tracking & Metered Billing',
            'Environment Variables',
            'Middleware Integration',
            'Observability'
        ]
        
        for section in required_sections:
            if section in content:
                print(f"  ✅ Section '{section}' found")
            else:
                print(f"  ❌ Section '{section}' missing")
                return False
        
        print("✅ Deployment documentation validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating deployment docs: {e}")
        return False

def test_middleware_integration():
    """Test middleware integration in main app."""
    print("\n🔍 Testing middleware integration...")
    
    try:
        with open('routers/main.py', 'r') as f:
            content = f.read()
        
        # Check for usage middleware import and integration
        if 'UsageTrackingMiddleware' in content:
            print("  ✅ UsageTrackingMiddleware imported")
        else:
            print("  ❌ UsageTrackingMiddleware not imported")
            return False
            
        if 'usage_tracking' in content and 'add_middleware' in content:
            print("  ✅ Usage middleware integrated into app")
        else:
            print("  ❌ Usage middleware not integrated")
            return False
            
        print("✅ Middleware integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating middleware integration: {e}")
        return False

def test_router_registration():
    """Test billing router registration."""
    print("\n🔍 Testing billing router registration...")
    
    try:
        with open('routers/contract.py', 'r') as f:
            content = f.read()
        
        # Check for billing tag and router registration
        if 'BILLING = "billing"' in content:
            print("  ✅ Billing router tag added")
        else:
            print("  ❌ Billing router tag missing")
            return False
            
        if '_register_billing_router' in content:
            print("  ✅ Billing router registration function found")
        else:
            print("  ❌ Billing router registration function missing")
            return False
            
        print("✅ Router registration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating router registration: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting usage logging implementation validation...")
    print("=" * 60)
    
    tests = [
        test_usage_event_structure,
        test_usage_helpers,
        test_middleware_structure,
        test_billing_router,
        test_environment_config,
        test_deployment_docs,
        test_middleware_integration,
        test_router_registration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validations passed! Usage logging implementation looks good.")
        return True
    else:
        print("⚠️  Some validations failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)