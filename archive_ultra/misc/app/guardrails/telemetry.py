# Compliance telemetry stubs
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ComplianceEvent:
    timestamp: datetime
    session_id: str
    request_id: str
    decision_action: str
    allowed: bool
    latency_ms: int

class ComplianceTelemetry:
    async def log_decision(self, event: ComplianceEvent) -> None:
        # Stub: integrate with your logging stack
        pass
