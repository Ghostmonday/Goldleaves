# === AGENT CONTEXT: SCHEMAS AGENT ===
# 🚧 TODOs for Phase 4 — Complete schema contracts
# - [x] Define all Pydantic schemas with type-safe fields
# - [x] Add pagination, response, and error wrapper patterns
# - [x] Validate alignment with models/ and services/ usage
# - [x] Enforce exports via `schemas/contract.py`
# - [x] Ensure each schema has at least one integration test
# - [x] Maintain strict folder isolation (no model/service imports)
# - [x] Add version string and export mapping to `SchemaContract`
# - [x] Annotate fields with metadata for future auto-docs

"""
Two-factor authentication schemas for enhanced security.
Provides schemas for TOTP, backup codes, and 2FA management.
"""

from pydantic import BaseModel, Field, validator, SecretStr
from typing import List, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    create_field_metadata
)


class TwoFactorMethod(str, Enum):
    """Two-factor authentication methods."""
    TOTP = "totp"  # Time-based One-Time Password (Google Authenticator, Authy, etc.)
    SMS = "sms"    # SMS-based codes
    EMAIL = "email"  # Email-based codes
    BACKUP_CODES = "backup_codes"  # Pre-generated backup codes
    HARDWARE_KEY = "hardware_key"  # Hardware security keys (U2F/WebAuthn)


class TwoFactorStatus(str, Enum):
    """Two-factor authentication status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING_SETUP = "pending_setup"
    SUSPENDED = "suspended"


class TwoFactorSetupRequest(BaseModel):
    """Schema for initiating 2FA setup."""
    
    method: TwoFactorMethod = Field(
        title="2FA Method", description="Type of two-factor authentication to set up"
    )
    
    phone_number: Optional[str] = Field(
        default=None,
        title="Phone Number", description="Phone number for SMS-based 2FA (required for SMS method)", example="+1234567890"
    )
    
    email: Optional[str] = Field(
        default=None,
        title="Email", description="Email address for email-based 2FA (required for email method)", example="user@example.com"
    )
    
    @validator('phone_number')
    def validate_phone_number(cls, v, values):
        """Validate phone number for SMS method."""
        if values.get('method') == TwoFactorMethod.SMS and not v:
            raise ValueError("Phone number is required for SMS 2FA")
        return v
    
    @validator('email')
    def validate_email(cls, v, values):
        """Validate email for email method."""
        if values.get('method') == TwoFactorMethod.EMAIL and not v:
            raise ValueError("Email is required for email 2FA")
        return v


class TwoFactorSetupResponse(BaseModel):
    """Schema for 2FA setup response."""
    
    setup_id: UUID = Field(
        description="Setup session identifier"
    )
    
    method: TwoFactorMethod = Field(
        title="Method", description="2FA method being set up"
    )
    
    qr_code_url: Optional[str] = Field(
        default=None,
        title="QR Code URL", description="QR code URL for TOTP setup", example="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    )
    
    secret_key: Optional[SecretStr] = Field(
        default=None,
        title="Secret Key", description="TOTP secret key (for manual entry)"
    )
    
    backup_codes: Optional[List[str]] = Field(
        default=None,
        **create_field_metadata(
            title="Backup Codes",
            description="One-time backup codes for recovery",
            example=["123456789", "987654321"]
        )
    )
    
    verification_required: bool = Field(
        title="Verification Required", description="Whether verification is needed to complete setup"
    )
    
    expires_at: datetime = Field(
        description="When this setup session expires"
    )
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }


class TwoFactorVerifyRequest(BaseModel):
    """Schema for verifying 2FA setup or authentication."""
    
    setup_id: Optional[UUID] = Field(
        default=None,
        title="Setup ID", description="Setup session ID (for completing setup)"
    )
    
    code: str = Field(
        min_length=4, max_length=20,
        title="Verification Code", description="2FA code from authenticator app, SMS, or backup code", example="123456"
    )
    
    method: Optional[TwoFactorMethod] = Field(
        default=None,
        title="Method", description="2FA method used (auto-detected if not provided)"
    )
    
    remember_device: bool = Field(
        default=False,
        title="Remember Device", description="Whether to remember this device for future logins"
    )
    
    @validator('code')
    def validate_code(cls, v):
        """Validate verification code format."""
        # Remove spaces and convert to string
        code = str(v).replace(' ', '')
        
        # Check if it's numeric (TOTP/SMS) or alphanumeric (backup code)
        if not (code.isdigit() or code.isalnum()):
            raise ValueError("Code must be numeric or alphanumeric")
        
        return code


class TwoFactorVerifyResponse(BaseModel):
    """Schema for 2FA verification response."""
    
    verified: bool = Field(
        title="Verified", description="Whether the code was valid"
    )
    
    method_enabled: bool = Field(
        default=False,
        title="Method Enabled", description="Whether 2FA method is now enabled (for setup completion)"
    )
    
    backup_codes_used: int = Field(
        default=0,
        title="Backup Codes Used", description="Number of backup codes consumed"
    )
    
    backup_codes_remaining: int = Field(
        default=0,
        title="Backup Codes Remaining", description="Number of backup codes remaining"
    )
    
    device_remembered: bool = Field(
        default=False,
        title="Device Remembered", description="Whether this device was remembered"
    )
    
    access_token: Optional[str] = Field(
        default=None,
        title="Access Token", description="JWT token if verification was for login"
    )


class TwoFactorMethodResponse(BaseModel):
    """Schema for 2FA method information."""
    
    id: UUID = Field(
        description="Method identifier"
    )
    
    method: TwoFactorMethod = Field(
        title="Method", description="2FA method type"
    )
    
    status: TwoFactorStatus = Field(
        title="Status", description="Current status of this method"
    )
    
    display_name: str = Field(
        title="Display Name", description="Human-readable name for this method", example="Google Authenticator"
    )
    
    masked_contact: Optional[str] = Field(
        default=None,
        title="Masked Contact", description="Masked phone/email for SMS/email methods", example="+1***-***-1234"
    )
    
    is_primary: bool = Field(
        default=False,
        title="Is Primary", description="Whether this is the primary 2FA method"
    )
    
    last_used_at: Optional[datetime] = Field(
        default=None,
        description="When this method was last used"
    )
    
    created_at: datetime = Field(
        description="When this method was set up"
    )
    
    backup_codes_count: Optional[int] = Field(
        default=None,
        title="Backup Codes Count", description="Number of unused backup codes (for backup_codes method)"
    )


class TwoFactorDisableRequest(BaseModel):
    """Schema for disabling 2FA."""
    
    method_id: Optional[UUID] = Field(
        default=None,
        title="Method ID", description="Specific method to disable (null to disable all)"
    )
    
    verification_code: str = Field(
        min_length=4, max_length=20,
        title="Verification Code", description="Current 2FA code to confirm disable action"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Optional reason for disabling 2FA"
    )


class TwoFactorBackupCodesResponse(BaseModel):
    """Schema for backup codes response."""
    
    codes: List[str] = Field(
        title="Backup Codes", description="List of backup codes for recovery"
    )
    
    total_codes: int = Field(
        title="Total Codes", description="Total number of backup codes generated"
    )
    
    used_codes: int = Field(
        default=0,
        title="Used Codes", description="Number of codes already used"
    )
    
    remaining_codes: int = Field(
        title="Remaining Codes", description="Number of unused codes"
    )
    
    generated_at: datetime = Field(
        description="When these codes were generated"
    )


class TwoFactorStatusResponse(BaseModel):
    """Schema for overall 2FA status."""
    
    enabled: bool = Field(
        title="Enabled", description="Whether 2FA is enabled for the user"
    )
    
    methods: List[TwoFactorMethodResponse] = Field(
        title="Methods", description="List of configured 2FA methods"
    )
    
    primary_method: Optional[TwoFactorMethodResponse] = Field(
        default=None,
        title="Primary Method", description="Primary 2FA method"
    )
    
    backup_codes_available: bool = Field(
        title="Backup Codes Available", description="Whether backup codes are configured"
    )
    
    last_verification: Optional[datetime] = Field(
        default=None,
        description="Last successful 2FA verification"
    )
    
    setup_required: bool = Field(
        default=False,
        title="Setup Required", description="Whether 2FA setup is required by organization policy"
    )


class TwoFactorRecoveryRequest(BaseModel):
    """Schema for 2FA recovery request."""
    
    email: str = Field(
        title="Email", description="Email address for account recovery", example="user@example.com"
    )
    
    recovery_method: str = Field(
        default="email",
        title="Recovery Method", description="Method to use for recovery (email, admin_override)"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Reason", description="Reason for requesting 2FA recovery"
    )
