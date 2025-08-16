from fastapi import APIRouter

router = APIRouter()

@router.get("/auth/ping")
async def auth_ping():
    return {"ok": True}


