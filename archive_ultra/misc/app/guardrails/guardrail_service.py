# SPEC + minimal working scaffold (safe defaults)
from dataclasses import dataclass
from typing import Literal, Optional, List, Dict
from enum import Enum
import re, hashlib, time, yaml, os

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Context:
    user_role: Literal["consumer", "attorney", "admin"] = "consumer"
    jurisdiction: Optional[str] = None  # e.g., "US-CA"
    intent: Literal["inform", "advise", "draft", "unknown"] = "unknown"
    utterance: str = ""
    session_id: str = ""
    request_id: str = ""
    metadata: Dict[str, str] = None

@dataclass
class Decision:
    allowed: bool
    action: str
    risk_level: RiskLevel
    reason: str
    mitigation: Optional[str] = None
    disclaimers: List[str] = None
    policy_refs: List[str] = None
    confidence: float = 1.0
    processing_time_ms: int = 0

class GuardrailService:
    """Deterministic evaluator over YAML policies (minimal MVP)."""
    def __init__(self, policy_dir: str = "compliance"):
        self.policy_dir = policy_dir
        self.policy = {}
        self.triggers = {"high_risk_verbs": [], "safer_patterns": []}
        self.allow_matrix = {}
        self.actions = {}
        self._load()

    def _load(self):
        contract_path = os.path.join(self.policy_dir, "upl_contract.yml")
        with open(contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.policy = data
        self.actions = {a["id"]: a for a in data.get("actions", [])}
        self.allow_matrix = data.get("allow_matrix", {})
        self.triggers = data.get("triggers", {"high_risk_verbs": [], "safer_patterns": []})
        self.enforcement_mode = data.get("enforcement_mode", "strict")

    def reload_policies(self):
        self._load()

    def _score_intent(self, text: str) -> str:
        # naive scoring based on triggers
        score = 0.0
        for t in self.triggers.get("high_risk_verbs", []):
            if re.search(t["pattern"], text, flags=re.I):
                score += t.get("weight", 0)
        for t in self.triggers.get("safer_patterns", []):
            if re.search(t["pattern"], text, flags=re.I):
                score += t.get("weight", 0)
        if score >= 0.7:
            return "advise"
        if score <= -0.4:
            return "inform"
        return "unknown"

    def _resolve_action(self, text: str, intent: str) -> str:
        if intent == "advise":
            # choose higher-risk actions by hints
            if re.search(r"\b(which form|what form|select form)\b", text, re.I):
                return "SelectForm"
            if re.search(r"\b(should I|what should|best strategy|beat this)\b", text, re.I):
                return "RecommendStrategy"
            if re.search(r"\b(can my .* do this|is it legal|interpret)\b", text, re.I):
                return "InterpretStatute"
            return "RecommendStrategy"
        if intent == "inform":
            if re.search(r"\bsteps? to file|how do I file\b", text, re.I):
                return "GiveFilingSteps"
            if re.search(r"\bwhat is|define|definition of\b", text, re.I):
                return "Explain"
            if re.search(r"\boptions|alternatives\b", text, re.I):
                return "OutlineOptions"
            return "Explain"
        return "Explain"

    def authorize(self, ctx: Context) -> Decision:
        start = time.time()
        text = ctx.utterance or ""
        intent = ctx.intent if ctx.intent != "unknown" else self._score_intent(text)
        action = self._resolve_action(text, intent)
        risk = RiskLevel(self.actions.get(action, {}).get("risk_level", "low").upper()) if self.actions.get(action) else RiskLevel.LOW
        policy = self.allow_matrix.get(action, {"default": "allowed", "rationale": ""})
        status = policy.get("default", "allowed")

        # enforcement logic
        if status == "deny" and self.enforcement_mode != "audit_only":
            ms = int((time.time() - start) * 1000)
            return Decision(
                allowed=False,
                action=action,
                risk_level=risk,
                reason=policy.get("rationale", "Denied by policy"),
                mitigation=policy.get("mitigation_template", ""),
                disclaimers=[],
                policy_refs=[f"upl_contract.yml#allow_matrix.{action}"],
                processing_time_ms=ms,
            )

        if status == "conditional":
            disclaimers = []
            for cond in policy.get("conditions", []):
                if cond.get("type") == "disclaimer_required":
                    disclaimers.append(cond.get("text", ""))
                if cond.get("type") == "jurisdiction_required" and not ctx.jurisdiction:
                    # missing jurisdiction → deny unless audit_only
                    if self.enforcement_mode == "audit_only":
                        continue
                    ms = int((time.time() - start) * 1000)
                    return Decision(
                        allowed=False,
                        action=action,
                        risk_level=risk,
                        reason="Jurisdiction required",
                        mitigation="Please specify your state or jurisdiction for general procedural information.",
                        disclaimers=[],
                        policy_refs=[f"upl_contract.yml#allow_matrix.{action}"],
                        processing_time_ms=ms,
                    )
            ms = int((time.time() - start) * 1000)
            return Decision(
                allowed=True,
                action=action,
                risk_level=risk,
                reason="Allowed with conditions",
                mitigation=None,
                disclaimers=disclaimers,
                policy_refs=[f"upl_contract.yml#allow_matrix.{action}"],
                processing_time_ms=ms,
            )

        # default allow
        ms = int((time.time() - start) * 1000)
        return Decision(
            allowed=True,
            action=action,
            risk_level=risk,
            reason="Allowed by default",
            mitigation=None,
            disclaimers=[],
            policy_refs=[f"upl_contract.yml#allow_matrix.{action}"],
            processing_time_ms=ms,
        )
