"""
Example usage of the billing system.
This file demonstrates how to integrate the billing functionality into your application.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db.session import get_db
from core.dependencies import get_current_active_user
from core.entitlements import requires_plan, requires_feature, EntitlementService
from models.user import User
from routers.billing import router as billing_router

# Create FastAPI app
app = FastAPI(title="Gold Leaves API with Billing")

# Include billing router
app.include_router(billing_router)


# Example: Protected endpoint requiring Pro or Team plan
@app.get("/api/premium-analytics")
@requires_plan("PRO", "TEAM")
def get_premium_analytics(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Premium analytics endpoint - requires Pro or Team plan."""
    return {
        "message": "Premium analytics data",
        "user_plan": user.id,
        "data": ["chart1", "chart2", "advanced_metrics"]
    }


# Example: Feature-specific protection
@app.get("/api/integrations")
@requires_feature("custom_integrations")
def get_custom_integrations(
    user: User = Depends(get_current_active_user)
):
    """Custom integrations - Team plan feature only."""
    return {
        "integrations": ["slack", "teams", "custom_webhook", "api_access"],
        "message": "Custom integrations available"
    }


# Example: Manual authorization with usage limits
@app.post("/api/process-data")
def process_data(
    data: dict,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process data with plan-based limits."""
    
    # Check API request limit
    monthly_limit = EntitlementService.get_feature_limit(
        user, "api_requests_per_month", default_limit=1000, db=db
    )
    
    # Here you would check current usage against the limit
    # For example, by querying a usage tracking table
    current_usage = get_current_monthly_usage(user.id)  # Your implementation
    
    if current_usage >= monthly_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly API limit of {monthly_limit} requests exceeded"
        )
    
    # Process the data
    result = process_user_data(data)  # Your implementation
    
    # Increment usage counter
    increment_usage_counter(user.id)  # Your implementation
    
    return {
        "result": result,
        "usage": {
            "current": current_usage + 1,
            "limit": monthly_limit,
            "remaining": monthly_limit - current_usage - 1
        }
    }


# Example: Organization-level feature check
@app.get("/api/team-dashboard")
def get_team_dashboard(
    org_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Team dashboard - requires team plan for the organization."""
    
    # Check if organization has team features
    has_team_features = EntitlementService.check_feature_access(
        user, "team_members", tenant_id=org_id, db=db
    )
    
    if not has_team_features:
        raise HTTPException(
            status_code=403,
            detail="Team dashboard requires Team plan for organization"
        )
    
    # Get team member limit
    team_limit = EntitlementService.get_feature_limit(
        user, "team_members", tenant_id=org_id, db=db
    )
    
    return {
        "dashboard": "team_metrics",
        "team_limit": team_limit,
        "features": ["analytics", "collaboration", "advanced_reports"]
    }


# Example: Dynamic plan information
@app.get("/api/plan-info")
def get_plan_info(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's plan information and feature access."""
    
    entitlement = EntitlementService.get_current_entitlement(
        user, tenant_id=user.organization_id, db=db
    )
    
    if not entitlement:
        return {
            "plan": "free",
            "features": {
                "api_requests_per_month": 1000,
                "storage_gb": 1,
                "team_members": 1,
                "advanced_analytics": False,
                "priority_support": False,
                "custom_integrations": False
            },
            "active": True,
            "upgrade_available": True
        }
    
    return {
        "plan": entitlement.plan.value,
        "features": entitlement.features,
        "active": entitlement.active,
        "seats": entitlement.seats,
        "upgrade_available": entitlement.plan.value != "team"
    }


# Placeholder functions - implement these based on your needs
def get_current_monthly_usage(user_id: int) -> int:
    """Get current month's API usage for user."""
    # Implement your usage tracking logic
    return 0

def process_user_data(data: dict) -> dict:
    """Process user data."""
    # Implement your data processing logic
    return {"processed": True, "result": "success"}

def increment_usage_counter(user_id: int) -> None:
    """Increment API usage counter for user."""
    # Implement your usage tracking logic
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)