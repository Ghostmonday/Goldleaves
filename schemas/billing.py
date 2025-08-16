# === AGENT CONTEXT: ROUTERS AGENT ===
# ✅ Phase 4: Billing schemas for checkout functionality

"""Pydantic schemas for billing and checkout functionality."""

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class PlanType(str, Enum):
    """Available subscription plans."""
    PRO = "Pro"
    TEAM = "Team"


class CheckoutRequestSchema(BaseModel):
    """Schema for checkout request."""
    plan: PlanType = Field(..., description="Subscription plan to checkout")

    class Config:
        json_schema_extra = {
            "example": {
                "plan": "Pro"
            }
        }


class CheckoutResponseSchema(BaseModel):
    """Schema for checkout response."""
    url: str = Field(..., description="Checkout session URL")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://checkout.stripe.com/pay/cs_test_a1b2c3d4e5f6"
            }
        }


class BillingSuccessSchema(BaseModel):
    """Schema for billing success page."""
    message: str = Field(default="Payment successful! Your subscription has been activated.")
    plan: str = Field(..., description="Activated subscription plan")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Payment successful! Your subscription has been activated.",
                "plan": "Pro"
            }
        }


class BillingCancelSchema(BaseModel):
    """Schema for billing cancel page."""
    message: str = Field(default="Payment cancelled. You can try again at any time.")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Payment cancelled. You can try again at any time."
            }
        }
