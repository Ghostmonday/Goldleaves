

"""Form model stubs for tests."""
from __future__ import annotations
from sqlalchemy import Column, Integer, String
from core.database import Base

class Form(Base):
	__tablename__ = "forms"
	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(255))
	status = Column(String(50), default="draft")

class FormType:
	BASIC = "BASIC"
	ADVANCED = "ADVANCED"

class FormStatus:
	DRAFT = "draft"
	PUBLISHED = "published"

class ContributorType:
	OWNER = "owner"
	COLLABORATOR = "collaborator"

class FormLanguage:
	EN = "en"
	ES = "es"


