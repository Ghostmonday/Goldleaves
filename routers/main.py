"""Application entrypoint with middleware wiring."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.stack import (
	correlation_id_middleware,
	request_timer_middleware,
	tenant_resolver_middleware,
)
from middleware.usage import usage_logger_middleware


def create_development_app() -> FastAPI:
	app = FastAPI(title="Backend API", version="1.0.0")

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Correct execution order: first registered runs first
	@app.middleware("http")
	async def correlation_middleware(request, call_next):
		return await correlation_id_middleware(request, call_next)

	@app.middleware("http")
	async def timer_middleware(request, call_next):
		return await request_timer_middleware(request, call_next)

	# Placeholder for auth middleware if needed

	@app.middleware("http")
	async def tenant_middleware(request, call_next):
		return await tenant_resolver_middleware(request, call_next)

	@app.middleware("http")
	async def usage_middleware(request, call_next):
		return await usage_logger_middleware(request, call_next)

	# Optional routers
	try:
		from .usage import router as usage_router
		app.include_router(usage_router, prefix="/usage", tags=["usage"])
	except Exception:
		pass
	try:
		from routers.billing import router as billing_router
		app.include_router(billing_router, prefix="/billing", tags=["billing"])
	except Exception:
		pass

	@app.get("/health")
	async def health_check():
		return {"status": "healthy"}

	@app.get("/")
	async def root():
		return {"message": "Backend API", "version": "1.0.0"}

	return app


app = create_development_app()


