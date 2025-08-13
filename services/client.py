

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.exceptions import NotFoundError, ValidationError
from models.client import Client


class ClientService:
	"""Minimal Client service shim for tests."""

	@staticmethod
	def create_client(db: Session, client_data: Any, organization_id: int, created_by_id: Optional[int] = None) -> Client:
		from models.client import ClientStatus, ClientType, ClientPriority, Language

		def _enum(enum_cls, val):
			if val is None:
				return None
			# Accept same class, different enum class with .value, or raw string
			if isinstance(val, enum_cls):
				return val
			if hasattr(val, "value"):
				return enum_cls(getattr(val, "value"))
			return enum_cls(val)

		slug = getattr(client_data, "slug", None) or Client.make_slug(client_data.first_name, client_data.last_name)
		client = Client(
			slug=slug,
			first_name=client_data.first_name,
			last_name=client_data.last_name,
			email=getattr(client_data, "email", None),
			phone=getattr(client_data, "phone", None),
			company_name=getattr(client_data, "company_name", None),
			notes=getattr(client_data, "notes", None),
			tags=getattr(client_data, "tags", []) or [],
			client_type=_enum(ClientType, getattr(client_data, "client_type", None) or ClientType.INDIVIDUAL.value),
			status=_enum(ClientStatus, getattr(client_data, "status", None) or ClientStatus.PROSPECT.value),
			priority=_enum(ClientPriority, getattr(client_data, "priority", None) or ClientPriority.MEDIUM.value),
			preferred_language=_enum(Language, getattr(client_data, "preferred_language", None) or Language.ENGLISH.value),
			assigned_to_id=getattr(client_data, "assigned_to_id", None),
			organization_id=organization_id,
			created_by_id=created_by_id,
		)
		client.update_full_name()
		db.add(client)
		db.commit()
		db.refresh(client)
		return client

	@staticmethod
	def list_clients(
		db: Session,
		organization_id: int,
		filters: Any,
		skip: int,
		limit: int,
		order_by: str,
		order_direction: str,
	) -> Tuple[List[Client], int]:
		q = db.query(Client).filter(Client.organization_id == organization_id)
		total = q.count()
		items = q.offset(skip).limit(limit).all()
		return items, total

	@staticmethod
	def search_clients(db: Session, organization_id: int, search_term: str, limit: int) -> List[Client]:
		return db.query(Client).filter(Client.organization_id == organization_id).limit(limit).all()

	@staticmethod
	def get_client(db: Session, client_id: int, organization_id: int) -> Optional[Client]:
		return db.query(Client).filter(Client.id == client_id, Client.organization_id == organization_id).first()

	@staticmethod
	def get_client_by_slug(db: Session, slug: str, organization_id: int) -> Optional[Client]:
		return db.query(Client).filter(Client.slug == slug, Client.organization_id == organization_id).first()

	@staticmethod
	def update_client(db: Session, client_id: int, client_update: Any, organization_id: int, updated_by_id: Optional[int] = None) -> Client:
		client = ClientService.get_client(db, client_id, organization_id)
		if not client:
			raise NotFoundError("Client not found")
		data = client_update.dict(exclude_unset=True)
		for k, v in data.items():
			setattr(client, k, v)
		client.update_full_name()
		db.add(client)
		db.commit()
		db.refresh(client)
		return client

	@staticmethod
	def delete_client(db: Session, client_id: int, organization_id: int) -> bool:
		client = ClientService.get_client(db, client_id, organization_id)
		if not client:
			raise NotFoundError("Client not found")
		db.delete(client)
		db.commit()
		return True

	@staticmethod
	def get_client_stats(db: Session, organization_id: int):
		return {
			"total_clients": db.query(Client).filter(Client.organization_id == organization_id).count(),
			"active_clients": 0,
			"by_type": {},
			"by_status": {},
		}

	@staticmethod
	def get_cases_for_client(db: Session, client_id: int, organization_id: int):
		# Avoid circular import at module top
		from models.case import Case
		return db.query(Case).filter(Case.client_id == client_id, Case.organization_id == organization_id).all()

	@staticmethod
	def bulk_update_clients(db: Session, bulk_action: Any, organization_id: int, updated_by_id: Optional[int] = None):
		return {"success_count": 0, "error_count": 0, "updated_clients": []}


