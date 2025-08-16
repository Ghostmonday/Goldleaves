from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from routers.usage import router as usage_router
from core.db.session import get_db
from core.config import settings
from apps.backend.models import User, RefreshToken
from apps.backend.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
    decode_token,
)


app = FastAPI()
app.include_router(usage_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- Minimal auth endpoints for tests -----------------
security = HTTPBearer(auto_error=False)


@app.post("/auth/register", status_code=201)
def register(payload: dict, db: Session = Depends(get_db)):
    # Very small schema validation
    for field in ("username", "email", "password"):
        if field not in payload:
            raise HTTPException(status_code=422, detail=f"Missing field: {field}")

    # Check duplicates
    if db.query(User).filter(User.email == payload["email"]).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # username may not exist on our stub; guard
    if hasattr(User, "username") and db.query(User).filter(getattr(User, "username") == payload["username"]).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=payload["email"],
        hashed_password=hash_password(payload["password"]),
        is_active=True,
    )
    if hasattr(User, "username"):
        setattr(user, "username", payload["username"])
    if hasattr(User, "is_verified"):
        setattr(user, "is_verified", False)
    if hasattr(User, "created_at"):
        from datetime import datetime
        setattr(user, "created_at", datetime.utcnow())
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user": {
            "id": user.id,
            "username": getattr(user, "username", payload["username"]),
            "email": user.email,
            "is_active": getattr(user, "is_active", True),
            "is_verified": getattr(user, "is_verified", False),
            "created_at": str(getattr(user, "created_at", "")),
        },
        "message": "User registered successfully",
    }


@app.post("/auth/login")
def login(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if hasattr(user, "is_active") and not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    if not verify_password(password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user.id)
    # Create a pseudo refresh token entry if model exists
    refresh_token_value = create_access_token(user.id, expires_minutes=60 * 24 * 30)
    try:
        rt = RefreshToken(user_id=user.id, token=refresh_token_value, is_active=True)
        if hasattr(RefreshToken, "expires_at"):
            from datetime import datetime, timedelta
            rt.expires_at = datetime.utcnow() + timedelta(days=30)
        db.add(rt)
        db.commit()
    except Exception:
        pass

    return {
        "access_token": access,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
        "expires_in": 60 * getattr(settings, "jwt_expiration_minutes", 30),
    }


@app.get("/auth/me")
def me(creds: HTTPAuthorizationCredentials | None = Depends(security)):
    if not creds or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.post("/auth/token/refresh")
def refresh_token(payload: dict, db: Session = Depends(get_db)):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Validate token structure
    try:
        data = decode_token(token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # Find token in DB
    db_token = None
    try:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    except Exception:
        pass
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    if hasattr(db_token, "expires_at") and db_token.expires_at and db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expired")

    # Verify user exists
    user = None
    try:
        user_id = int(data.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
    except Exception:
        pass
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Revoke old token if model supports it
    try:
        db_token.is_active = False
        db.add(db_token)
        db.commit()
    except Exception:
        pass

    access = create_access_token(user.id)
    new_refresh, exp = create_refresh_token(user.id)
    try:
        rt = RefreshToken(user_id=user.id, token=new_refresh, is_active=True, expires_at=exp)
        db.add(rt)
        db.commit()
    except Exception:
        pass

    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 60 * getattr(settings, "jwt_expiration_minutes", 30),
    }
