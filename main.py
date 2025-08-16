from fastapi import FastAPI

from routers.billing import router as billing_router
from routers.usage import router as usage_router
from routers.document import router as document_router
from routers.middleware import UsageMiddleware


app = FastAPI(title="App", version="0.1")
app.include_router(billing_router)
app.include_router(usage_router)
app.include_router(document_router)
app.add_middleware(UsageMiddleware)


@app.get("/health")
def health():
    return {"status": "ok"}
