from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class JurisdictionType(str, Enum):
	FEDERAL_DISTRICT = "federal_district"
	STATE_TRIAL = "state_trial"


class CourtDocumentType(str, Enum):
	BRIEF = "brief"


class PackagingStatus(str, Enum):
	COMPLETED = "completed"


class PackagingFlags(BaseModel):
	include_table_of_contents: bool = False
	include_certificate_of_service: bool = False
	create_filing_package: bool = False
	apply_jurisdiction_formatting: bool = False


class PackageMetadata(BaseModel):
	pass


class CaseInfo(BaseModel):
	case_number: str
	case_title: str
	court_name: str


class AttorneyInfo(BaseModel):
	attorney_name: str
	bar_number: str
	law_firm: str
	email: str
	phone: str


class CourtPackagingRequest(BaseModel):
	jurisdiction: JurisdictionType
	case_info: CaseInfo
	attorney_info: AttorneyInfo
	packaging_flags: PackagingFlags = PackagingFlags()


class JurisdictionValidation(BaseModel):
	valid: bool = True
	jurisdiction_compliant: bool = True
	jurisdiction_rules: List[str] = []


class CourtPackageResponse(BaseModel):
	package_id: str
	jurisdiction: JurisdictionType
	package_status: str = "completed"
	validation_passed: bool = True
	jurisdiction_compliant: bool = True
	package_file_path: Optional[str] = None
	manifest_file_path: Optional[str] = None
	files_included: List[str] = []


