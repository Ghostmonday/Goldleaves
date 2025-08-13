"""Application entrypoint (test stub)."""

from __future__ import annotations

from fastapi import FastAPI

from .usage import router as usage_router
from routers.billing import router as billing_router
from middleware.stack import tenant_resolver_middleware
from middleware.usage import usage_logger_middleware


def create_development_app():  # function expected by some tests
	app = FastAPI()
	app.include_router(usage_router)
	app.include_router(billing_router)
	# Wire middlewares in required order (tenant before usage)
	app.middleware("http")(tenant_resolver_middleware)
	app.middleware("http")(usage_logger_middleware)
	return app


app = create_development_app()


