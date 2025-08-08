# schemas/storage/court_packaging.py

"""Phase 7: Court-ready packaging schemas with jurisdiction-aware validation."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum


class JurisdictionType(str, Enum):
    """Legal jurisdictions for court packaging."""
    # Federal Courts
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_CIRCUIT = "federal_circuit"
    FEDERAL_SUPREME = "federal_supreme"
    FEDERAL_BANKRUPTCY = "federal_bankruptcy"
    FEDERAL_TAX = "federal_tax"
    
    # State Courts
    STATE_TRIAL = "state_trial"
    STATE_APPELLATE = "state_appellate"
    STATE_SUPREME = "state_supreme"
    STATE_FAMILY = "state_family"
    STATE_PROBATE = "state_probate"
    
    # Specialized Courts
    ARBITRATION = "arbitration"
    INTERNATIONAL = "international"
    ADMINISTRATIVE = "administrative"
    
    # International
    ICJ = "icj"  # International Court of Justice
    ICSID = "icsid"  # International Centre for Settlement of Investment Disputes
    

class CourtDocumentType(str, Enum):
    """Types of court documents for packaging."""
    COMPLAINT = "complaint"
    ANSWER = "answer"
    MOTION = "motion"
    BRIEF = "brief"
    MEMORANDUM = "memorandum"
    AFFIDAVIT = "affidavit"
    DECLARATION = "declaration"
    EXHIBIT = "exhibit"
    EVIDENCE = "evidence"
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    CORRESPONDENCE = "correspondence"
    EXPERT_REPORT = "expert_report"
    DEPOSITION = "deposition"
    DISCOVERY = "discovery"
    JUDGMENT = "judgment"
    ORDER = "order"
    SETTLEMENT = "settlement"
    APPEAL = "appeal"
    WRIT = "writ"


class PackagingStatus(str, Enum):
    """Status of court packaging process."""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PackagingFlags(BaseModel):
    """Flags for court packaging customization."""
    
    # Formatting flags
    include_line_numbers: bool = Field(True, description="Include line numbers in documents")
    double_spaced: bool = Field(True, description="Use double spacing")
    use_court_letterhead: bool = Field(False, description="Include court letterhead")
    include_certificate_of_service: bool = Field(True, description="Include certificate of service")
    
    # Content flags
    include_table_of_contents: bool = Field(True, description="Generate table of contents")
    include_table_of_authorities: bool = Field(True, description="Generate table of authorities")
    include_signature_pages: bool = Field(True, description="Include signature pages")
    include_appendices: bool = Field(True, description="Include appendices")
    
    # Security flags
    redact_sensitive_info: bool = Field(False, description="Redact sensitive information")
    apply_privilege_log: bool = Field(False, description="Apply attorney-client privilege log")
    include_confidentiality_notice: bool = Field(True, description="Include confidentiality notice")
    
    # E-filing flags
    create_filing_package: bool = Field(True, description="Create e-filing package")
    include_filing_receipt: bool = Field(False, description="Include filing receipt placeholder")
    generate_cm_ecf_format: bool = Field(False, description="Generate CM/ECF compatible format")
    
    # Validation flags
    validate_jurisdiction_rules: bool = Field(True, description="Validate against jurisdiction rules")
    check_formatting_compliance: bool = Field(True, description="Check formatting compliance")
    verify_document_completeness: bool = Field(True, description="Verify document completeness")


class CourtPackagingRequest(BaseModel):
    """Request schema for court-ready document packaging."""
    
    # Basic packaging information
    jurisdiction: JurisdictionType = Field(..., description="Target legal jurisdiction")
    court_name: str = Field(..., description="Specific court name")
    case_number: Optional[str] = Field(None, description="Court case number")
    case_title: str = Field(..., description="Case title or style")
    
    # Document classification
    document_type: CourtDocumentType = Field(..., description="Primary document type")
    document_title: str = Field(..., description="Document title for court filing")
    filing_date: Optional[date] = Field(None, description="Intended filing date")
    
    # Party information
    plaintiff_name: str = Field(..., description="Plaintiff name")
    defendant_name: str = Field(..., description="Defendant name")
    attorney_name: Optional[str] = Field(None, description="Attorney name")
    attorney_bar_number: Optional[str] = Field(None, description="Attorney bar number")
    law_firm_name: Optional[str] = Field(None, description="Law firm name")
    
    # Packaging options
    packaging_flags: PackagingFlags = Field(default_factory=PackagingFlags, description="Packaging customization flags")
    custom_formatting: Optional[Dict[str, Any]] = Field(None, description="Custom formatting options")
    
    # Version and content selection
    include_version_history: bool = Field(False, description="Include version history as appendix")
    include_audit_trail: bool = Field(False, description="Include audit trail as appendix")
    version_range: Optional[Dict[str, int]] = Field(None, description="Version range to package")
    
    # Output preferences
    output_format: str = Field("pdf", description="Primary output format")
    bundle_format: str = Field("zip", description="Bundle format for multiple files")
    filename_prefix: Optional[str] = Field(None, description="Custom filename prefix")
    
    # Security and compliance
    encryption_required: bool = Field(False, description="Require encryption for output")
    watermark_text: Optional[str] = Field(None, description="Watermark text for documents")
    confidentiality_level: str = Field("public", description="Confidentiality classification")
    
    # Metadata
    packaging_reason: str = Field(..., description="Reason for packaging")
    notes: Optional[str] = Field(None, description="Additional packaging notes")
    
    @validator('case_number')
    def validate_case_number(cls, v, values):
        """Validate case number format based on jurisdiction."""
        if not v:
            return v
        
        jurisdiction = values.get('jurisdiction')
        if jurisdiction and jurisdiction.startswith('federal_'):
            # Federal case number format validation
            import re
            if not re.match(r'^\d{1,2}:\d{2}-[a-zA-Z]{2}-\d{4,6}(-[a-zA-Z]{1,3})?$', v):
                raise ValueError("Federal case number format should be: YY:YY-XX-NNNNNN or similar")
        
        return v
    
    @validator('attorney_bar_number')
    def validate_bar_number(cls, v):
        """Validate attorney bar number format."""
        if v and not v.replace('-', '').replace(' ', '').isalnum():
            raise ValueError("Bar number should contain only alphanumeric characters, hyphens, and spaces")
        return v


class JurisdictionValidation(BaseModel):
    """Validation rules for specific jurisdictions."""
    
    jurisdiction: JurisdictionType = Field(..., description="Target jurisdiction")
    
    # Document requirements
    max_page_count: Optional[int] = Field(None, description="Maximum page count")
    required_margins_inches: Optional[Dict[str, float]] = Field(None, description="Required margins")
    required_font_size: Optional[int] = Field(None, description="Required font size")
    required_font_family: Optional[List[str]] = Field(None, description="Allowed font families")
    
    # Formatting requirements
    line_spacing_required: Optional[float] = Field(None, description="Required line spacing")
    page_numbering_required: bool = Field(True, description="Page numbering requirement")
    header_footer_required: bool = Field(False, description="Header/footer requirement")
    
    # Filing requirements
    requires_table_of_contents: bool = Field(False, description="Table of contents requirement")
    requires_table_of_authorities: bool = Field(False, description="Table of authorities requirement")
    requires_certificate_of_service: bool = Field(True, description="Certificate of service requirement")
    requires_signature_block: bool = Field(True, description="Signature block requirement")
    
    # E-filing specifics
    supports_electronic_filing: bool = Field(True, description="Electronic filing support")
    max_file_size_mb: Optional[int] = Field(None, description="Maximum file size in MB")
    allowed_file_formats: List[str] = Field(default_factory=lambda: ["pdf"], description="Allowed file formats")
    
    # Security requirements
    encryption_required: bool = Field(False, description="Encryption requirement")
    redaction_required: bool = Field(False, description="Redaction requirement for certain info")
    watermark_required: bool = Field(False, description="Watermark requirement")
    
    # Custom validation rules
    custom_rules: Dict[str, Any] = Field(default_factory=dict, description="Jurisdiction-specific custom rules")


class PackageMetadata(BaseModel):
    """Metadata for generated court packages."""
    
    # Package identification
    package_id: str = Field(..., description="Unique package identifier")
    document_id: int = Field(..., description="Source document ID")
    jurisdiction: JurisdictionType = Field(..., description="Target jurisdiction")
    
    # Generation information
    generated_at: datetime = Field(..., description="Package generation timestamp")
    generated_by: str = Field(..., description="User who generated package")
    packaging_version: str = Field(..., description="Packaging engine version")
    
    # Court information
    court_name: str = Field(..., description="Target court name")
    case_number: Optional[str] = Field(None, description="Case number")
    case_title: str = Field(..., description="Case title")
    document_type: CourtDocumentType = Field(..., description="Document type")
    
    # Package contents
    files_included: List[str] = Field(..., description="Files included in package")
    total_pages: int = Field(..., description="Total page count")
    total_file_size: int = Field(..., description="Total package size in bytes")
    
    # Validation results
    validation_passed: bool = Field(..., description="Whether validation passed")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    jurisdiction_compliant: bool = Field(..., description="Jurisdiction compliance status")
    
    # Formatting applied
    formatting_applied: Dict[str, Any] = Field(..., description="Formatting transformations applied")
    flags_used: PackagingFlags = Field(..., description="Packaging flags used")
    
    # Security and integrity
    package_hash: str = Field(..., description="Package integrity hash")
    encryption_applied: bool = Field(..., description="Whether encryption was applied")
    watermark_applied: bool = Field(..., description="Whether watermarking was applied")
    digital_signature: Optional[str] = Field(None, description="Digital signature if applied")
    
    # Lineage preservation
    source_versions: List[int] = Field(..., description="Source document versions included")
    audit_events_included: int = Field(0, description="Number of audit events included")
    collaboration_data_included: bool = Field(False, description="Whether collaboration data included")
    
    # E-filing preparation
    efiling_ready: bool = Field(..., description="Whether package is e-filing ready")
    filing_format: Optional[str] = Field(None, description="E-filing format used")
    filing_metadata: Dict[str, Any] = Field(default_factory=dict, description="E-filing metadata")


class CourtPackageResponse(BaseModel):
    """Response for court packaging operations."""
    
    # Package identification
    package_id: str = Field(..., description="Generated package identifier")
    document_id: int = Field(..., description="Source document ID")
    packaging_status: PackagingStatus = Field(..., description="Packaging status")
    
    # Package results
    package_metadata: Optional[PackageMetadata] = Field(None, description="Package metadata")
    package_files: List[str] = Field(default_factory=list, description="Generated package files")
    manifest_file: Optional[str] = Field(None, description="Package manifest file")
    
    # Download information
    package_download_url: Optional[str] = Field(None, description="Package download URL")
    manifest_download_url: Optional[str] = Field(None, description="Manifest download URL")
    download_expires_at: Optional[datetime] = Field(None, description="Download URL expiration")
    
    # Processing information
    processing_duration_ms: int = Field(..., description="Processing duration")
    queue_position: Optional[int] = Field(None, description="Queue position if pending")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Status details
    success: bool = Field(..., description="Whether packaging succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    
    # Validation results
    jurisdiction_validation: Optional[JurisdictionValidation] = Field(None, description="Applied validation rules")
    validation_report: Dict[str, Any] = Field(default_factory=dict, description="Detailed validation report")
    
    # Progress tracking
    progress_percentage: int = Field(0, ge=0, le=100, description="Processing progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    
    created_at: datetime = Field(..., description="Response creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Predefined jurisdiction validation rules
JURISDICTION_RULES = {
    JurisdictionType.FEDERAL_DISTRICT: JurisdictionValidation(
        jurisdiction=JurisdictionType.FEDERAL_DISTRICT,
        max_page_count=None,
        required_margins_inches={"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        required_font_size=12,
        required_font_family=["Times New Roman", "Times", "serif"],
        line_spacing_required=2.0,
        page_numbering_required=True,
        requires_table_of_contents=True,
        requires_table_of_authorities=True,
        supports_electronic_filing=True,
        max_file_size_mb=50,
        allowed_file_formats=["pdf"]
    ),
    
    JurisdictionType.STATE_TRIAL: JurisdictionValidation(
        jurisdiction=JurisdictionType.STATE_TRIAL,
        max_page_count=50,
        required_margins_inches={"top": 1.0, "bottom": 1.0, "left": 1.25, "right": 1.0},
        required_font_size=12,
        required_font_family=["Times New Roman", "Arial", "Calibri"],
        line_spacing_required=1.5,
        page_numbering_required=True,
        requires_certificate_of_service=True,
        supports_electronic_filing=True,
        max_file_size_mb=25
    ),
    
    JurisdictionType.ARBITRATION: JurisdictionValidation(
        jurisdiction=JurisdictionType.ARBITRATION,
        required_font_size=11,
        line_spacing_required=1.15,
        page_numbering_required=True,
        requires_table_of_contents=False,
        requires_certificate_of_service=False,
        supports_electronic_filing=True,
        allowed_file_formats=["pdf", "docx"]
    )
}


def get_jurisdiction_rules(jurisdiction: JurisdictionType) -> JurisdictionValidation:
    """Get validation rules for a specific jurisdiction."""
    return JURISDICTION_RULES.get(
        jurisdiction,
        JurisdictionValidation(jurisdiction=jurisdiction)  # Default rules
    )
