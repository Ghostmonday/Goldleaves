import os
import time
import logging
from typing import List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apps.backend.api.routers import ping, auth
from apps.backend.api.routers.token_refresh import router as token_refresh_router
from apps.backend.api.routers.verification import router as verification_router
from core.config import settings, validate_config
from core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gold Leaves API",
    description="API for Gold Leaves application",
    version="1.0.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {duration:.3f}s"
    )
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": "1.0.0"
    }

app.include_router(ping.router, prefix="/ping", tags=["Ping"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(token_refresh_router, prefix="/auth", tags=["Auth"])
app.include_router(verification_router, prefix="/auth/verify", tags=["Email Verification"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    if not validate_config():
        logger.warning("Configuration validation found issues")
    if settings.is_development:
        logger.info("Creating database tables...")
        init_db()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Gold Leaves API shutting down...")