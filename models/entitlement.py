"""
Entitlement model for managing user and tenant billing plans and features.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    JSON, UniqueConstraint, Index, CheckConstraint, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel, TimestampMixin


class PlanType(PyEnum):
    """Available subscription plans."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class Entitlement(BaseModel):
    """
    Model for managing user and tenant entitlements/subscriptions.
    Supports both user-level and tenant-level entitlements.
    """
    __tablename__ = "entitlements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys - either user_id or tenant_id should be set, not both
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=True,
        comment="User this entitlement belongs to (for user-level plans)"
    )
    tenant_id = Column(
        Integer, 
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=True,
        comment="Organization/tenant this entitlement belongs to (for team plans)"
    )
    
    # Plan details
    plan = Column(
        Enum(PlanType), 
        default=PlanType.FREE, 
        nullable=False,
        comment="Subscription plan type"
    )
    seats = Column(
        Integer, 
        default=1, 
        nullable=False,
        comment="Number of seats/users allowed"
    )
    features = Column(
        JSON, 
        default=dict, 
        nullable=False,
        comment="JSON object containing enabled features and limits"
    )
    
    # Stripe integration
    stripe_customer_id = Column(
        String(255), 
        nullable=True,
        index=True,
        comment="Stripe customer ID"
    )
    stripe_subscription_id = Column(
        String(255), 
        nullable=True,
        index=True,
        comment="Stripe subscription ID"
    )
    
    # Status
    active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Whether the entitlement is currently active"
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Organization", foreign_keys=[tenant_id])
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure either user_id or tenant_id is set, but not both
        CheckConstraint(
            "(user_id IS NULL) != (tenant_id IS NULL)",
            name="check_user_or_tenant_not_both"
        ),
        # Unique constraint to prevent duplicate entitlements
        UniqueConstraint(
            "user_id", "tenant_id", 
            name="uq_entitlement_user_tenant"
        ),
        # Performance indexes
        Index("idx_entitlement_user_active", "user_id", "active"),
        Index("idx_entitlement_tenant_active", "tenant_id", "active"),
        Index("idx_entitlement_plan_active", "plan", "active"),
        Index("idx_entitlement_stripe_customer", "stripe_customer_id"),
        Index("idx_entitlement_stripe_subscription", "stripe_subscription_id"),
        # Ensure seats is positive
        CheckConstraint("seats > 0", name="check_seats_positive"),
    )
    
    def __repr__(self) -> str:
        """String representation of the entitlement."""
        target = f"user_id={self.user_id}" if self.user_id else f"tenant_id={self.tenant_id}"
        return (
            f"<Entitlement(id={self.id}, {target}, plan={self.plan.value}, "
            f"seats={self.seats}, active={self.active})>"
        )
    
    @property
    def is_user_level(self) -> bool:
        """Check if this is a user-level entitlement."""
        return self.user_id is not None
    
    @property
    def is_tenant_level(self) -> bool:
        """Check if this is a tenant/organization-level entitlement."""
        return self.tenant_id is not None
    
    def get_feature(self, feature_name: str, default: Any = None) -> Any:
        """Get a specific feature value from the features JSON."""
        if not self.features:
            return default
        return self.features.get(feature_name, default)
    
    def set_feature(self, feature_name: str, value: Any) -> None:
        """Set a specific feature value in the features JSON."""
        if not self.features:
            self.features = {}
        self.features[feature_name] = value
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return self.get_feature(feature_name, False) is True
    
    @classmethod
    def get_default_features(cls, plan: PlanType) -> Dict[str, Any]:
        """Get default features for a given plan."""
        features = {
            PlanType.FREE: {
                "api_requests_per_month": 1000,
                "storage_gb": 1,
                "team_members": 1,
                "advanced_analytics": False,
                "priority_support": False,
                "custom_integrations": False,
            },
            PlanType.PRO: {
                "api_requests_per_month": 50000,
                "storage_gb": 100,
                "team_members": 5,
                "advanced_analytics": True,
                "priority_support": True,
                "custom_integrations": False,
            },
            PlanType.TEAM: {
                "api_requests_per_month": 200000,
                "storage_gb": 500,
                "team_members": 25,
                "advanced_analytics": True,
                "priority_support": True,
                "custom_integrations": True,
            },
        }
        return features.get(plan, features[PlanType.FREE])
    
    def activate(self) -> None:
        """Activate this entitlement."""
        self.active = True
    
    def deactivate(self) -> None:
        """Deactivate this entitlement."""
        self.active = False
    
    def update_from_stripe_subscription(
        self, 
        stripe_subscription_id: str, 
        stripe_customer_id: str, 
        plan: PlanType
    ) -> None:
        """Update entitlement from Stripe subscription data."""
        self.stripe_subscription_id = stripe_subscription_id
        self.stripe_customer_id = stripe_customer_id
        self.plan = plan
        self.features = self.get_default_features(plan)
        self.activate()