# schemas/client/core.py

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..base.responses import PaginatedResponse


class ClientType(str, Enum):
    """Client type enumeration."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    NONPROFIT = "nonprofit"
    GOVERNMENT = "government"


class ClientStatus(str, Enum):
    """Client status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    FORMER = "former"
    BLOCKED = "blocked"


class ClientPriority(str, Enum):
    """Client priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Language(str, Enum):
    """Language enumeration."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"


class AddressBase(BaseModel):
    """Base address schema."""
    line1: Optional[str] = Field(None, max_length=255, description="Address line 1")
    line2: Optional[str] = Field(None, max_length=255, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state_province: Optional[str] = Field(None, max_length=100, description="State or province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")


class ClientBase(BaseModel):
    """Base client schema with common fields."""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    
    # Organization/Business information
    company_name: Optional[str] = Field(None, max_length=200, description="Company name")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    
    # Client metadata
    client_type: ClientType = Field(ClientType.INDIVIDUAL, description="Type of client")
    status: ClientStatus = Field(ClientStatus.PROSPECT, description="Client status")
    priority: ClientPriority = Field(ClientPriority.MEDIUM, description="Priority level")
    preferred_language: Language = Field(Language.ENGLISH, description="Preferred language")
    
    # Notes and external references
    notes: Optional[str] = Field(None, description="General notes")
    external_id: Optional[str] = Field(None, max_length=100, description="External system ID")
    source: Optional[str] = Field(None, max_length=100, description="How client was acquired")
    referral_source: Optional[str] = Field(None, max_length=200, description="Referral source")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and len(v.strip()) == 0:
            return None
        return v
    
    @validator('email')
    def validate_email_not_empty(cls, v):
        """Ensure email is not empty string."""
        if v and len(v.strip()) == 0:
            return None
        return v


class ClientCreate(ClientBase):
    """Schema for creating a new client."""
    address: Optional[AddressBase] = Field(None, description="Client address")
    tags: Optional[List[str]] = Field(default_factory=list, description="Client tags")
    assigned_to_id: Optional[int] = Field(None, description="ID of assigned user")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "phone": "+1-555-123-4567",
                "company_name": "Smith & Associates",
                "client_type": "business",
                "status": "prospect",
                "priority": "medium",
                "preferred_language": "en",
                "notes": "Potential client for contract review",
                "source": "referral",
                "referral_source": "Jane Doe",
                "address": {
                    "line1": "123 Business St",
                    "city": "New York",
                    "state_province": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "tags": ["corporate", "contracts"]
            }
        }


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[datetime] = None
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    priority: Optional[ClientPriority] = None
    preferred_language: Optional[Language] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    external_id: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=100)
    referral_source: Optional[str] = Field(None, max_length=200)
    address: Optional[AddressBase] = None
    tags: Optional[List[str]] = None
    assigned_to_id: Optional[int] = None


class ClientContactInfo(BaseModel):
    """Client contact information schema."""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[AddressBase] = None


class ClientResponse(ClientBase):
    """Schema for client response."""
    id: int
    slug: str
    full_name: Optional[str]
    organization_id: int
    created_by_id: Optional[int]
    assigned_to_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Address information
    address: Optional[AddressBase] = None
    
    # Additional fields
    tags: List[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    
    # Computed fields
    display_name: Optional[str] = None
    contact_info: Optional[ClientContactInfo] = None
    case_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "slug": "john-smith-123",
                "first_name": "John",
                "last_name": "Smith",
                "full_name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "+1-555-123-4567",
                "company_name": "Smith & Associates",
                "client_type": "business",
                "status": "active",
                "priority": "medium",
                "preferred_language": "en",
                "display_name": "John Smith",
                "case_count": 3,
                "organization_id": 1,
                "created_at": "2025-08-02T10:00:00Z",
                "updated_at": "2025-08-02T10:00:00Z"
            }
        }


class ClientSummary(BaseModel):
    """Simplified client schema for lists and references."""
    id: int
    slug: str
    full_name: Optional[str]
    display_name: str
    email: Optional[str]
    client_type: ClientType
    status: ClientStatus
    priority: ClientPriority
    case_count: int = 0
    
    class Config:
        from_attributes = True


class ClientListResponse(PaginatedResponse):
    """Paginated list of clients."""
    items: List[ClientResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "slug": "john-smith-123",
                        "full_name": "John Smith",
                        "display_name": "John Smith",
                        "email": "john.smith@example.com",
                        "client_type": "business",
                        "status": "active",
                        "priority": "medium",
                        "case_count": 3
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10,
                "pages": 1
            }
        }


class ClientFilter(BaseModel):
    """Client filtering parameters."""
    search: Optional[str] = Field(None, description="Search in name, email, company")
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    priority: Optional[ClientPriority] = None
    assigned_to_id: Optional[int] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "search": "smith",
                "client_type": "business",
                "status": "active",
                "priority": "high",
                "tags": ["corporate", "litigation"]
            }
        }


class ClientStats(BaseModel):
    """Client statistics schema."""
    total_clients: int = 0
    active_clients: int = 0
    prospects: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    recent_clients: int = 0  # Last 30 days
    
    class Config:
        schema_extra = {
            "example": {
                "total_clients": 150,
                "active_clients": 120,
                "prospects": 30,
                "by_type": {
                    "individual": 80,
                    "business": 60,
                    "nonprofit": 10
                },
                "by_status": {
                    "active": 120,
                    "prospect": 30
                },
                "by_priority": {
                    "low": 50,
                    "medium": 70,
                    "high": 25,
                    "urgent": 5
                },
                "recent_clients": 12
            }
        }


class ClientBulkAction(BaseModel):
    """Schema for bulk client actions."""
    client_ids: List[int] = Field(..., min_items=1, description="List of client IDs")
    action: str = Field(..., description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "client_ids": [1, 2, 3],
                "action": "update_status",
                "parameters": {
                    "status": "active"
                }
            }
        }


class ClientBulkResult(BaseModel):
    """Result of bulk client operations."""
    success_count: int = 0
    error_count: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    updated_clients: List[int] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "success_count": 2,
                "error_count": 1,
                "errors": [
                    {
                        "client_id": 3,
                        "error": "Client not found"
                    }
                ],
                "updated_clients": [1, 2]
            }
        }
