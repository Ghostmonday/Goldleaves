# models/contract.py
"""
Models Agent Contract Definition
Phase 4: Complete model contracts for Goldleaves backend

This file defines the contract interface for the models agent,
ensuring compliance with the Goldleaves architecture.
"""

from typing import Dict, List, Any
# Contract keys for model validation
MODEL_CONTRACTS = {
    "User": {
        "required_fields": [
            "id", "email", "hashed_password", "is_active", "is_verified", 
            "is_admin", "email_verified", "status", "created_at", "updated_at"
        ],
        "optional_fields": [
            "last_login", "login_count", "organization_id", "deleted_at", "is_deleted"
        ],
        "relationships": ["revoked_tokens", "organization", "api_keys"],
        "methods": [
            "update_login_timestamp", "activate", "deactivate", "suspend", 
            "verify_email", "soft_delete", "restore"
        ]
    },
    "Organization": {
        "required_fields": [
            "id", "name", "plan", "is_active", "created_at", "updated_at"
        ],
        "optional_fields": [
            "description", "deleted_at", "is_deleted"
        ],
        "relationships": ["users", "api_keys"],
        "methods": ["soft_delete", "restore"]
    },
    "RevokedToken": {
        "required_fields": [
            "id", "token", "token_type", "revoked_at", "expires_at", 
            "user_id", "created_at", "updated_at"
        ],
        "optional_fields": [],
        "relationships": ["user"],
        "methods": []
    },
    "APIKey": {
        "required_fields": [
            "id", "key", "name", "scope", "is_active", "user_id", 
            "created_at", "updated_at", "usage_count"
        ],
        "optional_fields": [
            "description", "expires_at", "last_used_at", "organization_id",
            "deleted_at", "is_deleted"
        ],
        "relationships": ["user", "organization"],
        "methods": ["update_usage", "is_expired", "soft_delete", "restore"]
    }
}

# Enum contracts for schema alignment
ENUM_CONTRACTS = {
    "UserStatus": ["ACTIVE", "INACTIVE", "SUSPENDED", "DELETED"],
    "OrganizationPlan": ["FREE", "BASIC", "PRO", "ENTERPRISE"],
    "APIKeyScope": ["READ", "WRITE", "ADMIN", "FULL_ACCESS"]
}

# Index contracts for performance optimization
INDEX_CONTRACTS = {
    "organizations": [
        "idx_org_name_active",
        "idx_org_plan_active"
    ],
    "users": [
        "idx_user_email_active",
        "idx_user_status_active", 
        "idx_user_org_status",
        "idx_user_admin_active"
    ],
    "revoked_tokens": [
        "idx_token_expires",
        "idx_user_token_type",
        "idx_token_type_active"
    ],
    "api_keys": [
        "idx_key_active",
        "idx_user_scope_active",
        "idx_org_scope_active",
        "idx_expires_active"
    ]
}

# Constraint contracts
CONSTRAINT_CONTRACTS = {
    "password_constraints": ["check_password_length"],
    "email_constraints": ["check_email_format"]
}

def validate_model_contract(model_name: str, model_class: Any) -> bool:
    """Validate that a model class adheres to its contract."""
    if model_name not in MODEL_CONTRACTS:
        return False
    
    contract = MODEL_CONTRACTS[model_name]
    
    # Check required fields exist
    for field in contract["required_fields"]:
        if not hasattr(model_class, field):
            return False
    
    # Check relationships exist
    for rel in contract["relationships"]:
        if not hasattr(model_class, rel):
            return False
    
    # Check methods exist
    for method in contract["methods"]:
        if not hasattr(model_class, method):
            return False
    
    return True

def get_test_coverage_targets() -> Dict[str, List[str]]:
    """Return test coverage targets for each model."""
    return {
        "User": [
            "test_user_creation",
            "test_user_login_tracking", 
            "test_user_status_management",
            "test_user_soft_delete",
            "test_user_email_verification"
        ],
        "Organization": [
            "test_organization_creation",
            "test_organization_user_relationships",
            "test_organization_soft_delete"
        ],
        "RevokedToken": [
            "test_token_revocation",
            "test_token_expiration"
        ],
        "APIKey": [
            "test_api_key_creation",
            "test_api_key_usage_tracking",
            "test_api_key_expiration"
        ]
    }
