

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

# Use the same Base as tests import (models.user.Base)
from .user import Base  # type: ignore


class ClientType(PyEnum):
	INDIVIDUAL = "individual"
	BUSINESS = "business"
	NONPROFIT = "nonprofit"
	GOVERNMENT = "government"


class ClientStatus(PyEnum):
	ACTIVE = "active"
	INACTIVE = "inactive"
	PROSPECT = "prospect"
	FORMER = "former"
	BLOCKED = "blocked"


class ClientPriority(PyEnum):
	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"
	URGENT = "urgent"


class Language(PyEnum):
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


class Client(Base):  # type: ignore
	__tablename__ = "clients"

	id = Column(Integer, primary_key=True, autoincrement=True)
	slug = Column(String(255), unique=True, index=True, nullable=False)

	# Names and contact
	first_name = Column(String(100), nullable=False)
	last_name = Column(String(100), nullable=False)
	full_name = Column(String(255), nullable=True)
	email = Column(String(255), nullable=True)
	phone = Column(String(50), nullable=True)

	company_name = Column(String(200), nullable=True)
	job_title = Column(String(100), nullable=True)

	client_type = Column(Enum(ClientType), nullable=False, default=ClientType.INDIVIDUAL)
	status = Column(Enum(ClientStatus), nullable=False, default=ClientStatus.PROSPECT)
	priority = Column(Enum(ClientPriority), nullable=False, default=ClientPriority.MEDIUM)
	preferred_language = Column(Enum(Language), nullable=False, default=Language.ENGLISH)

	notes = Column(Text, nullable=True)
	internal_notes = Column(Text, nullable=True)
	tags = Column(JSON, nullable=True)

	# Organization and audit
	organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
	created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
	assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

	created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
	updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
	is_deleted = Column(Boolean, nullable=False, default=False)

	# Relationships
	cases = relationship("Case", back_populates="client")
	created_by = relationship("User", foreign_keys=[created_by_id])
	assigned_to = relationship("User", foreign_keys=[assigned_to_id])
	organization = relationship("Organization")

	def update_full_name(self) -> None:
		self.full_name = f"{self.first_name} {self.last_name}".strip()

	@staticmethod
	def make_slug(first_name: str, last_name: str) -> str:
		base = f"{first_name}-{last_name}".lower().strip().replace(" ", "-")
		import re
		base = re.sub(r"[^a-z0-9\-]", "", base)
		return base[:240]


