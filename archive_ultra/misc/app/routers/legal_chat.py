from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import authorize_request
from app.guardrails.filters import OutputFilter

router = APIRouter(prefix="/api", tags=["legal-chat"])

class ChatMessage(BaseModel):
    message: str

async def generate_response(msg: ChatMessage) -> str:
    # Placeholder: replace with your AI generation callchain
    # For demo, just echo
    return f"Info: {msg.message}"

@router.post("/chat")
async def chat_endpoint(msg: ChatMessage, decision=Depends(authorize_request)):
    # If policy denies, return mitigation text
    if not decision.allowed:
        return {
            "content": decision.mitigation or "This request cannot be fulfilled under the compliance policy.",
            "compliance": {
                "action": decision.action,
                "reason": decision.reason,
                "risk_level": decision.risk_level.value,
                "policy_refs": decision.policy_refs
            }
        }
    # Otherwise, produce content and sanitize + inject disclaimers
    content = await generate_response(msg)
    content = OutputFilter.sanitize(content, decision)
    content = OutputFilter.inject_disclaimers(content, decision.disclaimers or [])
    return {
        "content": content,
        "compliance": {
            "action": decision.action,
            "reason": decision.reason,
            "risk_level": decision.risk_level.value,
            "policy_refs": decision.policy_refs
        }
    }
