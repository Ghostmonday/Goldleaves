"""Usage example for integrating UsageMiddleware into a FastAPI application."""

from fastapi import FastAPI
from app.usage.middleware import UsageMiddleware
import core.usage

# Create FastAPI app
app = FastAPI(title="My API with Usage Tracking")

# Add the UsageMiddleware to track request latency and results
app.add_middleware(UsageMiddleware)

# Define your regular endpoints
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Optional: Add an endpoint to view usage statistics (for debugging/monitoring)
@app.get("/admin/usage-stats")
async def get_usage_stats():
    """Get current usage statistics (for development/debugging only)."""
    events = core.usage.get_events()
    
    # Basic statistics
    total_requests = len(events)
    successful_requests = len([e for e in events if e["result"] == "success"])
    error_requests = len([e for e in events if e["result"] == "error"])
    
    if events:
        avg_latency = sum(e["latency_ms"] for e in events) / len(events)
        max_latency = max(e["latency_ms"] for e in events)
    else:
        avg_latency = max_latency = 0
    
    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "error_requests": error_requests,
        "average_latency_ms": round(avg_latency, 2),
        "max_latency_ms": max_latency,
        "recent_events": events[-10:]  # Last 10 events
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)