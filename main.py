# main.py

"""Main application entry point for Goldleaves backend."""

from routers.main import app

# Export app for ASGI servers like uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
