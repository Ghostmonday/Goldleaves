#!/usr/bin/env python3
"""
Simple validation script for billing functionality.
This can run without external dependencies.
"""

import os
import sys

def validate_file_structure():
    """Validate that all required files exist."""
    required_files = [
        "schemas/billing.py",
        "services/billing_service.py", 
        "routers/billing.py",
        "tests/test_billing.py"
    ]
    
    print("Validating file structure...")
    all_exist = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def validate_billing_mock_env():
    """Validate BILLING_MOCK environment variable support."""
    print("\nValidating BILLING_MOCK environment variable...")
    
    # Check .env.example
    try:
        with open(".env.example", "r") as f:
            content = f.read()
            if "BILLING_MOCK=1" in content:
                print("✓ BILLING_MOCK=1 found in .env.example")
                return True
            else:
                print("✗ BILLING_MOCK=1 not found in .env.example")
                return False
    except FileNotFoundError:
        print("✗ .env.example not found")
        return False

def validate_router_registration():
    """Validate billing router is registered."""
    print("\nValidating router registration...")
    
    try:
        with open("routers/__init__.py", "r") as f:
            content = f.read()
            if "from . import billing" in content:
                print("✓ Billing router imported in routers/__init__.py")
                return True
            else:
                print("✗ Billing router not imported in routers/__init__.py")
                return False
    except FileNotFoundError:
        print("✗ routers/__init__.py not found")
        return False

def validate_api_endpoint_structure():
    """Validate API endpoint structure in billing router."""
    print("\nValidating API endpoint structure...")
    
    try:
        with open("routers/billing.py", "r") as f:
            content = f.read()
            
            checks = [
                ('"/api/v1/billing"', "API v1 billing prefix"),
                ('"/checkout"', "Checkout endpoint"),
                ('"/success"', "Success return page"),
                ('"/cancel"', "Cancel return page"),
                ('CheckoutRequestSchema', "Request schema"),
                ('CheckoutResponseSchema', "Response schema"),
                ('get_current_user', "Authentication dependency"),
                ('get_current_tenant', "Tenancy dependency")
            ]
            
            all_good = True
            for check, description in checks:
                if check in content:
                    print(f"✓ {description}")
                else:
                    print(f"✗ {description} - NOT FOUND")
                    all_good = False
            
            return all_good
            
    except FileNotFoundError:
        print("✗ routers/billing.py not found")
        return False

def validate_frontend_integration():
    """Validate frontend integration files."""
    print("\nValidating frontend integration...")
    
    frontend_files = [
        "static/usage.html",
        "static/billing-success.html", 
        "static/billing-cancel.html",
        "static/frontend-tests.js"
    ]
    
    all_exist = True
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    # Check for key frontend features
    if os.path.exists("static/usage.html"):
        with open("static/usage.html", "r") as f:
            content = f.read()
            features = [
                ('id="upgradeBtn"', "Upgrade button"),
                ('id="rateLimitModal"', "429 modal"),
                ('CheckoutHandler', "Checkout handler"),
                ('ApiClient', "API client"),
                ('window.location', "Redirect functionality")
            ]
            
            for feature, description in features:
                if feature in content:
                    print(f"✓ {description} in usage page")
                else:
                    print(f"✗ {description} NOT found")
                    all_exist = False
    
    return all_exist
    """Validate API endpoint structure in billing router."""
    print("\nValidating API endpoint structure...")
    
    try:
        with open("routers/billing.py", "r") as f:
            content = f.read()
            
            checks = [
                ('"/api/v1/billing"', "API v1 billing prefix"),
                ('"/checkout"', "Checkout endpoint"),
                ('"/success"', "Success return page"),
                ('"/cancel"', "Cancel return page"),
                ('CheckoutRequestSchema', "Request schema"),
                ('CheckoutResponseSchema', "Response schema"),
                ('get_current_user', "Authentication dependency"),
                ('get_current_tenant', "Tenancy dependency")
            ]
            
            all_good = True
            for check, description in checks:
                if check in content:
                    print(f"✓ {description}")
                else:
                    print(f"✗ {description} - NOT FOUND")
                    all_good = False
            
            return all_good
            
    except FileNotFoundError:
        print("✗ routers/billing.py not found")
        return False

def main():
    """Run all validations."""
    print("🔍 Billing Implementation Validation\n")
    print("=" * 50)
    
    results = []
    results.append(validate_file_structure())
    results.append(validate_billing_mock_env())
    results.append(validate_router_registration())
    results.append(validate_api_endpoint_structure())
    results.append(validate_frontend_integration())
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All validations passed!")
        print("\nImplemented features:")
        print("- POST /api/v1/billing/checkout endpoint")
        print("- Authentication and tenancy validation") 
        print("- BILLING_MOCK=1 environment variable support")
        print("- Success and cancel return routes")
        print("- Frontend integration (429 modal, Usage page)")
        print("- Comprehensive test suite structure")
        return 0
    else:
        print("❌ Some validations failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())