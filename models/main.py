# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from models.core_db import engine
from models.user import Base

# ✅ Phase 3: Auth router import and inclusion - COMPLETED
from models.auth_router import router as auth_router

# ✅ Phase 4: Client and Case router imports - NEW
from routers.client import router as client_router
from routers.case import router as case_router

app = FastAPI(
    title="Goldleaves Backend API",
    description="Backend API for Goldleaves application with user management and authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
# ✅ Phase 3: Auth router included and properly structured
app.include_router(auth_router)

# ✅ Phase 4: Client and Case routers included - NEW
app.include_router(client_router, prefix="/api")
app.include_router(case_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Goldleaves Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# ✅ Phase 3: All main.py TODOs completed
