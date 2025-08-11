"""
Entitlement management and authorization decorators.
"""

import functools
import logging
from typing import List, Optional, Union, Callable, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_active_user
from models.entitlement import Entitlement, PlanType
from models.user import User

logger = logging.getLogger(__name__)


class EntitlementService:
    """Service for managing entitlements and checking permissions."""
    
    @staticmethod
    def get_current_entitlement(
        user: User,
        tenant_id: Optional[int] = None,
        db: Session = None
    ) -> Optional[Entitlement]:
        """
        Get the current active entitlement for a user or tenant.
        
        Args:
            user: Current user
            tenant_id: Optional tenant ID for organization-level entitlements
            db: Database session
            
        Returns:
            Active entitlement or None
        """
        if not db:
            from core.db.session import get_db as get_db_session
            db = next(get_db_session())
        
        # If tenant_id is provided, look for organization-level entitlement first
        if tenant_id:
            org_entitlement = db.query(Entitlement).filter(
                Entitlement.tenant_id == tenant_id,
                Entitlement.active == True,
                Entitlement.is_deleted == False
            ).first()
            
            if org_entitlement:
                return org_entitlement
        
        # Fall back to user-level entitlement
        user_entitlement = db.query(Entitlement).filter(
            Entitlement.user_id == user.id,
            Entitlement.active == True,
            Entitlement.is_deleted == False
        ).first()
        
        return user_entitlement
    
    @staticmethod
    def check_plan_access(
        user: User,
        required_plans: List[PlanType],
        tenant_id: Optional[int] = None,
        db: Session = None
    ) -> bool:
        """
        Check if user has access to one of the required plans.
        
        Args:
            user: Current user
            required_plans: List of acceptable plans
            tenant_id: Optional tenant ID
            db: Database session
            
        Returns:
            True if user has access to at least one required plan
        """
        entitlement = EntitlementService.get_current_entitlement(user, tenant_id, db)
        
        if not entitlement:
            # No entitlement found, check if FREE is in required plans
            return PlanType.FREE in required_plans
        
        return entitlement.plan in required_plans
    
    @staticmethod
    def check_feature_access(
        user: User,
        feature_name: str,
        tenant_id: Optional[int] = None,
        db: Session = None
    ) -> bool:
        """
        Check if user has access to a specific feature.
        
        Args:
            user: Current user
            feature_name: Name of the feature to check
            tenant_id: Optional tenant ID
            db: Database session
            
        Returns:
            True if user has access to the feature
        """
        entitlement = EntitlementService.get_current_entitlement(user, tenant_id, db)
        
        if not entitlement:
            # No entitlement, use FREE plan defaults
            free_features = Entitlement.get_default_features(PlanType.FREE)
            return free_features.get(feature_name, False)
        
        return entitlement.has_feature(feature_name)
    
    @staticmethod
    def get_feature_limit(
        user: User,
        feature_name: str,
        default_limit: int = 0,
        tenant_id: Optional[int] = None,
        db: Session = None
    ) -> int:
        """
        Get the limit for a specific feature.
        
        Args:
            user: Current user
            feature_name: Name of the feature
            default_limit: Default limit if feature not found
            tenant_id: Optional tenant ID
            db: Database session
            
        Returns:
            Feature limit value
        """
        entitlement = EntitlementService.get_current_entitlement(user, tenant_id, db)
        
        if not entitlement:
            # No entitlement, use FREE plan defaults
            free_features = Entitlement.get_default_features(PlanType.FREE)
            return free_features.get(feature_name, default_limit)
        
        return entitlement.get_feature(feature_name, default_limit)


def requires_plan(
    *allowed_plans: Union[str, PlanType],
    tenant_id_param: Optional[str] = None
) -> Callable:
    """
    Decorator to require specific subscription plans.
    
    Args:
        *allowed_plans: Plans that are allowed (e.g., "PRO", "TEAM", PlanType.PRO)
        tenant_id_param: Optional parameter name for tenant ID in the route
        
    Usage:
        @requires_plan("PRO", "TEAM")
        def some_premium_endpoint():
            pass
            
        @requires_plan(PlanType.TEAM, tenant_id_param="org_id") 
        def team_only_endpoint(org_id: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get dependencies
            user = kwargs.get('current_user')
            if not user:
                # Try to inject user dependency if not present
                try:
                    user = get_current_active_user()
                    kwargs['current_user'] = user
                except:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
            
            # Get tenant ID if specified
            tenant_id = None
            if tenant_id_param and tenant_id_param in kwargs:
                tenant_id = kwargs[tenant_id_param]
            
            # Convert plan strings to enum
            required_plans = []
            for plan in allowed_plans:
                if isinstance(plan, str):
                    try:
                        required_plans.append(PlanType(plan.lower()))
                    except ValueError:
                        logger.error(f"Invalid plan type in decorator: {plan}")
                        continue
                elif isinstance(plan, PlanType):
                    required_plans.append(plan)
            
            if not required_plans:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No valid plans specified in decorator"
                )
            
            # Check access
            from core.db.session import get_db as get_db_session
            db = kwargs.get('db') or next(get_db_session())
            has_access = EntitlementService.check_plan_access(
                user=user,
                required_plans=required_plans,
                tenant_id=tenant_id,
                db=db
            )
            
            if not has_access:
                plan_names = [plan.value.upper() for plan in required_plans]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required plan: {' or '.join(plan_names)}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def requires_feature(feature_name: str, tenant_id_param: Optional[str] = None) -> Callable:
    """
    Decorator to require specific features.
    
    Args:
        feature_name: Name of the required feature
        tenant_id_param: Optional parameter name for tenant ID in the route
        
    Usage:
        @requires_feature("advanced_analytics")
        def analytics_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get dependencies
            user = kwargs.get('current_user')
            if not user:
                try:
                    user = get_current_active_user()
                    kwargs['current_user'] = user
                except:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
            
            # Get tenant ID if specified
            tenant_id = None
            if tenant_id_param and tenant_id_param in kwargs:
                tenant_id = kwargs[tenant_id_param]
            
            # Check feature access
            from core.db.session import get_db as get_db_session
            db = kwargs.get('db') or next(get_db_session())
            has_access = EntitlementService.check_feature_access(
                user=user,
                feature_name=feature_name,
                tenant_id=tenant_id,
                db=db
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required feature: {feature_name}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Dependency functions for FastAPI
def get_current_entitlement(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Optional[Entitlement]:
    """FastAPI dependency to get current user's entitlement."""
    return EntitlementService.get_current_entitlement(user, db=db)


def get_current_entitlement_with_tenant(
    tenant_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Optional[Entitlement]:
    """FastAPI dependency to get current entitlement with tenant context."""
    return EntitlementService.get_current_entitlement(user, tenant_id, db)


# Export main functions
__all__ = [
    "EntitlementService",
    "requires_plan", 
    "requires_feature",
    "get_current_entitlement",
    "get_current_entitlement_with_tenant"
]