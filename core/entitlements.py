"""Core entitlements module for plan limits and usage tracking."""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Plan limits configuration
PLAN_LIMITS = {
    "Free": {"unit": "api_calls", "soft": 500, "hard": 750},
    "Pro": {"unit": "api_calls", "soft": 5000, "hard": 7500},
    "Team": {"unit": "api_calls", "soft": 20000, "hard": 30000},
}

class PlanType(str, Enum):
    """Enumeration of available plan types."""
    FREE = "Free"
    PRO = "Pro"
    TEAM = "Team"

@dataclass
class PlanLimits:
    """Data class representing plan limits."""
    unit: str
    soft: int
    hard: int

@dataclass
class UsageInfo:
    """Data class representing current usage information."""
    current_usage: int
    plan: str
    unit: str
    soft_cap: int
    hard_cap: int
    remaining: int

# In-memory storage for usage tracking (would be replaced with proper storage in production)
_usage_storage: Dict[str, int] = {}

def get_plan_limits(plan: str) -> Optional[PlanLimits]:
    """Get plan limits for a specific plan.
    
    Args:
        plan: The plan name (Free, Pro, Team)
        
    Returns:
        PlanLimits object or None if plan not found
    """
    if plan not in PLAN_LIMITS:
        return None
    
    limits = PLAN_LIMITS[plan]
    return PlanLimits(
        unit=limits["unit"],
        soft=limits["soft"],
        hard=limits["hard"]
    )

def get_tenant_plan(tenant_id: str) -> str:
    """Get the plan for a tenant.
    
    In a real implementation, this would query a database or service.
    For now, we'll use a simple mapping with Free as default.
    
    Args:
        tenant_id: The tenant identifier
        
    Returns:
        The plan name (defaults to "Free")
    """
    # Simple mapping for demo purposes
    # In production, this would query actual tenant data
    tenant_plans = {
        "tenant_pro": "Pro",
        "tenant_team": "Team",
    }
    return tenant_plans.get(tenant_id, "Free")

def get_current_usage(tenant_id: str, unit: str = "api_calls") -> int:
    """Get current usage for a tenant.
    
    Args:
        tenant_id: The tenant identifier
        unit: The usage unit (default: "api_calls")
        
    Returns:
        Current usage count
    """
    key = f"{tenant_id}:{unit}"
    return _usage_storage.get(key, 0)

def increment_usage(tenant_id: str, unit: str = "api_calls", increment: int = 1) -> int:
    """Increment usage for a tenant.
    
    Args:
        tenant_id: The tenant identifier
        unit: The usage unit (default: "api_calls")
        increment: Amount to increment (default: 1)
        
    Returns:
        New usage count
    """
    key = f"{tenant_id}:{unit}"
    current = _usage_storage.get(key, 0)
    new_usage = current + increment
    _usage_storage[key] = new_usage
    return new_usage

def get_usage_info(tenant_id: str) -> UsageInfo:
    """Get complete usage information for a tenant.
    
    Args:
        tenant_id: The tenant identifier
        
    Returns:
        UsageInfo object with current usage and limits
    """
    plan = get_tenant_plan(tenant_id)
    limits = get_plan_limits(plan)
    
    if not limits:
        # Fallback to Free plan if plan not found
        limits = get_plan_limits("Free")
    
    current_usage = get_current_usage(tenant_id, limits.unit)
    remaining = max(limits.hard - current_usage, 0)
    
    return UsageInfo(
        current_usage=current_usage,
        plan=plan,
        unit=limits.unit,
        soft_cap=limits.soft,
        hard_cap=limits.hard,
        remaining=remaining
    )

def reset_usage(tenant_id: str, unit: str = "api_calls") -> None:
    """Reset usage for a tenant (useful for testing).
    
    Args:
        tenant_id: The tenant identifier
        unit: The usage unit (default: "api_calls")
    """
    key = f"{tenant_id}:{unit}"
    if key in _usage_storage:
        del _usage_storage[key]

def reset_all_usage() -> None:
    """Reset all usage data (useful for testing)."""
    _usage_storage.clear()