from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from models.document import Document, DocumentVersion, DocumentCorrection


class DocumentService:
	@staticmethod
	def create_document(db: Session, document_data, organization_id: int, created_by_id: int) -> Document:
		doc = Document(
			title=document_data.title,
			document_type=str(getattr(document_data, "document_type", "contract")),
			status=str(getattr(document_data, "status", "draft")),
			confidentiality=str(getattr(document_data, "confidentiality", "internal")),
			case_id=getattr(document_data, "case_id", None),
			client_id=getattr(document_data, "client_id", None),
			content=getattr(document_data, "content", None),
			ai_predictions=getattr(document_data, "ai_predictions", None),
			prediction_score=getattr(document_data, "prediction_score", None),
			organization_id=organization_id,
			created_by_id=created_by_id,
			version=1,
		)
		db.add(doc)
		db.commit()
		db.refresh(doc)
		return doc

	@staticmethod
	def update_document(db: Session, document_id: int, document_update, organization_id: int, updated_by_id: int) -> Document:
		doc = db.query(Document).filter(Document.id == document_id).first()
		if not doc:
			return None
		if getattr(document_update, "title", None):
			doc.title = document_update.title
		if getattr(document_update, "status", None):
			doc.status = str(document_update.status)
		if getattr(document_update, "confidentiality", None):
			doc.confidentiality = str(document_update.confidentiality)
		doc.version = (doc.version or 1) + 1
		db.commit()
		db.refresh(doc)
		return doc

	@staticmethod
	def ingest_prediction(db: Session, document_id: int, prediction_ingest, organization_id: int, ingested_by_id: int) -> Document:
		doc = db.query(Document).filter(Document.id == document_id).first()
		if not doc:
			return None
		pdata = prediction_ingest.prediction_data
		doc.ai_predictions = {
			"model_name": pdata.model_name,
			"model_version": pdata.model_version,
			"overall_confidence": pdata.overall_confidence,
		}
		doc.prediction_score = float(pdata.overall_confidence)
		# Keep pending status
		doc.version = (doc.version or 1) + 1
		# snapshot version
		db.add(DocumentVersion(
			document_id=doc.id,
			version_number=doc.version,
			title=doc.title,
			content=doc.content,
			prediction_status=str(getattr(doc, "prediction_status", "pending")),
			prediction_score=doc.prediction_score,
			change_summary="Prediction ingested",
			change_reason="AI prediction",
			changed_by_id=ingested_by_id,
		))
		db.commit()
		db.refresh(doc)
		return doc

	@staticmethod
	def apply_correction(db: Session, document_id: int, correction_data, organization_id: int, corrected_by_id: int) -> Document:
		doc = db.query(Document).filter(Document.id == document_id).first()
		if not doc:
			return None
		# Update doc status to partially_confirmed
		setattr(doc, "prediction_status", "partially_confirmed")
		# Create correction records
		for c in correction_data.corrections:
			db.add(DocumentCorrection(
				document_id=doc.id,
				field_path=c.field_path,
				original_value=str(getattr(c, "original_value", "")),
				corrected_value=str(getattr(c, "corrected_value", "")),
				confidence_before=int((getattr(c, "confidence_before", 0) or 0) * 100),
				confidence_after=int((getattr(c, "confidence_after", 0) or 0) * 100),
				correction_reason=getattr(c, "correction_reason", ""),
				correction_type=str(getattr(c, "correction_type", "edit")).lower().replace("correctiontype.", ""),
				corrected_by_id=corrected_by_id,
				review_status="approved",
			))
		doc.version = (doc.version or 1) + 1
		db.commit()
		db.refresh(doc)
		return doc

	@staticmethod
	def list_documents(db: Session, organization_id: int, filters) -> Tuple[List[Document], int]:
		q = db.query(Document)
		if getattr(filters, "min_prediction_score", None) is not None:
			q = q.filter(Document.prediction_score >= float(filters.min_prediction_score))
		if getattr(filters, "prediction_status", None):
			q = q.filter(Document.status != None)  # simple placeholder
		docs = q.all()
		return docs, len(docs)

	@staticmethod
	def get_document(db: Session, doc_id: int, organization_id: int) -> Document:
		return db.query(Document).filter(Document.id == doc_id).first()

	@staticmethod
	def get_audit_trail(db: Session, document_id: int, organization_id: int) -> Dict[str, Any]:
		versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).all()
		return {
			"document_id": document_id,
			"current_version": versions[0].version_number if versions else 1,
			"recent_versions": [
				{"version_number": v.version_number, "change_summary": v.change_summary}
				for v in versions[:5]
			],
			"recent_corrections": [],
		}

	@staticmethod
	def bulk_update_documents(db: Session, bulk_action, organization_id: int, updated_by_id: int):
		from pydantic import BaseModel

		class Result(BaseModel):
			success_count: int
			error_count: int
			updated_documents: List[int]

		ids = getattr(bulk_action, "document_ids", [])
		for doc_id in ids:
			doc = db.query(Document).filter(Document.id == doc_id).first()
			if not doc:
				continue
			if getattr(bulk_action, "action", "") == "update_status":
				params = getattr(bulk_action, "parameters", {}) or {}
				status = params.get("status")
				if status:
					doc.status = status
		db.commit()
		return Result(success_count=len(ids), error_count=0, updated_documents=ids)


