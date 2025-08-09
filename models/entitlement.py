# models/entitlement.py
"""Entitlement model for storing Stripe subscription and billing data."""

from __future__ import annotations
from sqlalchemy import Column, String, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

# Import from local dependencies
from .dependencies import Base, utcnow


class PlanType(PyEnum):
    """Enum for subscription plan types."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class Entitlement(Base):
    """Model for storing customer entitlements and billing information."""
    
    __tablename__ = "entitlements"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: f"ent_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}")
    
    # Tenant/Organization identification
    tenant_id = Column(String, nullable=False, index=True)
    
    # Stripe customer and subscription data
    customer_id = Column(String, nullable=True, index=True)  # Stripe customer ID
    subscription_id = Column(String, nullable=True, index=True)  # Stripe subscription ID
    
    # Plan and billing cycle information
    plan = Column(Enum(PlanType), nullable=False, default=PlanType.FREE)
    cycle_start = Column(DateTime(timezone=True), nullable=True)
    cycle_end = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    # Table arguments for indexes
    __table_args__ = (
        Index('idx_entitlement_tenant', 'tenant_id'),
        Index('idx_entitlement_customer', 'customer_id'),
        Index('idx_entitlement_subscription', 'subscription_id'),
        Index('idx_entitlement_plan', 'plan'),
    )
    
    def __repr__(self):
        return f"<Entitlement(id={self.id}, tenant_id={self.tenant_id}, plan={self.plan.value})>"
    
    @property
    def is_active(self) -> bool:
        """Check if the entitlement is currently active."""
        if not self.cycle_end:
            return self.plan != PlanType.FREE
        return datetime.utcnow() <= self.cycle_end.replace(tzinfo=None)
    
    @property
    def is_expired(self) -> bool:
        """Check if the entitlement has expired."""
        if not self.cycle_end:
            return False
        return datetime.utcnow() > self.cycle_end.replace(tzinfo=None)
    
    def get_plan_limits(self) -> dict:
        """Get plan-specific limits and capabilities."""
        if self.plan == PlanType.FREE:
            return {
                "max_documents": 5,
                "max_collaborators": 1,
                "storage_gb": 1,
                "features": ["basic_templates"]
            }
        elif self.plan == PlanType.PRO:
            return {
                "max_documents": 100,
                "max_collaborators": 5,
                "storage_gb": 10,
                "features": ["basic_templates", "advanced_templates", "ai_assistance"]
            }
        elif self.plan == PlanType.TEAM:
            return {
                "max_documents": 1000,
                "max_collaborators": 25,
                "storage_gb": 100,
                "features": ["basic_templates", "advanced_templates", "ai_assistance", "team_management", "advanced_analytics"]
            }
        else:
            return self.get_plan_limits()  # Default to free plan
    
    def can_perform_action(self, action: str, current_usage: dict = None) -> bool:
        """Check if the current plan allows a specific action."""
        limits = self.get_plan_limits()
        current_usage = current_usage or {}
        
        if action == "create_document":
            return current_usage.get("document_count", 0) < limits["max_documents"]
        elif action == "add_collaborator":
            return current_usage.get("collaborator_count", 0) < limits["max_collaborators"]
        elif action == "upload_file":
            return current_usage.get("storage_used_gb", 0) < limits["storage_gb"]
        elif action.startswith("use_feature_"):
            feature = action.replace("use_feature_", "")
            return feature in limits["features"]
        
        return True  # Allow unknown actions by default