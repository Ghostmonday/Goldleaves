from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def ping():
    return {
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }
