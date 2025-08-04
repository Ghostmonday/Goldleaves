from typing import List, Optional
class UserLoginRequest(BaseModel):
    """Request payload for user authentication."""
class TokenResponse(BaseModel):
    """Response with access and refresh tokens.
    
    Contains JWT tokens for authentication and session management.
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token for obtaining new access tokens")
    token_type: str = Field(default="bearer", description="Type of token issued")
    expires_in: int = Field(
        default=3600, 
        description="Token expiration time in seconds",
        gt=0
    )
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "def5020089c5c43ea5f999aef4...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_verified": True,
                    "created_at": "2025-08-01T12:00:00",
                    "last_login": "2025-08-01T14:30:00",
                    "role": "user"
                }
            }
        }

# Password Reset Schemas

class PasswordResetRequest(BaseModel):
    """Request to initiate password reset process."""
class EmailVerificationToken(BaseModel):
    """Schema for email verification token data.
    
    This represents the token payload used for email verification.
    """
    user_id: int = Field(..., description="User ID for verification", gt=0)
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    token_type: str = Field(default="email_verification", description="Type of verification token")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": 1,
                "email": "user@example.com",
                "expires_at": "2025-08-03T12:00:00Z",
                "token_type": "email_verification"
            }
        }

# Refresh Token Schema

class RefreshTokenRequest(BaseModel):
    """Request to refresh an expired access token."""
    refresh_token: str = Field(..., description="Refresh token provided during authentication")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "def5020089c5c43ea5f999aef4..."
            }
        }

# Multi-factor Authentication Schemas

class MFASetupResponse(BaseModel):
    """Response for MFA setup process containing setup information."""
    secret: str = Field(..., description="TOTP secret key for authenticator app")
    qr_code_url: str = Field(..., description="URL for QR code to scan with authenticator app")
    backup_codes: List[str] = Field(..., description="One-time backup codes for recovery")
    
    class Config:
        schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code_url": "otpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example",
                "backup_codes": ["123456", "789012", "345678", "456789", "012345"]
            }
        }

class MFAVerifyRequest(BaseModel):
    """Request to verify a TOTP code during MFA setup or login."""
    code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        description="6-digit TOTP code from authenticator app"
    )
    backup_code: Optional[str] = Field(None, description="Alternative backup code if TOTP is unavailable")
    
    @validator('code')
    def validate_totp_code(cls, v):
        """Validate TOTP code format."""
        if not v.isdigit():
            raise ValueError('TOTP code must contain only digits')
        return v
    
    @root_validator
    def validate_code_or_backup(cls, values):
        """Ensure either code or backup_code is provided."""
        code = values.get('code')
        backup_code = values.get('backup_code')
        
        if not code and not backup_code:
            raise ValueError('Either TOTP code or backup code must be provided')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "code": "123456",
                "backup_code": None
            }
        }


# Administrative User Management Schemas

class AdminUserCreateRequest(BaseModel):
    """Request payload for admin to create a new user account.
    
    This schema provides administrators with comprehensive options for creating
    user accounts, including role assignment, status control, and optional
    password generation.
    """
    "UserLoginRequest", 
    "UserResponse",
    "TokenResponse",
    "UserProfileUpdate",
    "UserPasswordUpdate",
    "UserListParams",
    
    # Password Management
    "PasswordResetRequest",
    "PasswordResetVerify",
    
    "EmailVerificationToken",
    "RefreshTokenRequest",
    "MFASetupResponse",
    "MFAVerifyRequest",
    
    # Admin Operations
    "AdminUserCreateRequest",
    "AdminUserResponse",
    "AdminUserUpdateRequest",
    "BulkUserActionRequest",
    "UserSearchRequest",
    
    # Supporting Types
    "UserSecurityInfo",
    "UserSessionInfo"
]