# FastAPI DI for guardrails (wire this into routes as needed)
from fastapi import Request, Depends
from .guardrails.guardrail_service import GuardrailService, Context, Decision

_service = GuardrailService(policy_dir="compliance")

async def get_guardrail_service() -> GuardrailService:
    return _service

async def authorize_request(
    request: Request,
    service: GuardrailService = Depends(get_guardrail_service)
) -> Decision:
    body = await request.body()
    text = body.decode('utf-8', errors='ignore')
    ctx = Context(
        user_role="consumer",
        jurisdiction=None,
        intent="unknown",
        utterance=text[:2000],  # truncate for safety
        session_id=request.headers.get("X-Session-Id",""),
        request_id=request.headers.get("X-Request-Id",""),
        metadata={"ua": request.headers.get("User-Agent","")}
    )
    decision = service.authorize(ctx)
    # stash on request for handlers to use
    request.state.compliance_decision = decision
    return decision
