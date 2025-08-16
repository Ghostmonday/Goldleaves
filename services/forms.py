from __future__ import annotations

import secrets
from typing import Any


class FormService:
	def __init__(self, db: Any):
		self.db = db

	def _generate_form_id(self) -> str:
		return f"form_{secrets.token_hex(6)}"

	def _generate_feedback_id(self) -> str:
		return f"fb_{secrets.token_hex(6)}"

	def _calculate_feedback_priority(self, feedback_type: str, severity: int) -> str:
		if feedback_type == "field_error":
			if severity >= 5:
				return "critical"
			if severity >= 3:
				return "high"
			return "medium"
		# default path
		if severity >= 4:
			return "high"
		if severity >= 3:
			return "medium"
		return "low"


