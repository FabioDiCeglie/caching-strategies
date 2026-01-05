"""
Mini-Project 2: Rate Limiter with Redis
Uses Redis INCR for atomic counter-based rate limiting.
"""

from fastapi import FastAPI, HTTPException, Request, Depends
import redis
import time
import os
from datetime import datetime

app = FastAPI(
    title="Redis Rate Limiter Demo",
    description="Simple rate limiter using Redis INCR",
    version="1.0.0"
)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

RATE_LIMIT = 5
WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> dict:
    """Simple fixed window rate limiter using Redis INCR"""
    now = datetime.now()
    current_minute = now.strftime("%Y-%m-%d-%H-%M")
    key = f"rate_limit:{user_id}:{current_minute}"
    
    current = redis_client.incr(key)
    
    if current == 1:
        redis_client.expire(key, WINDOW_SECONDS)
    
    allowed = current <= RATE_LIMIT
    remaining = max(0, RATE_LIMIT - current)
    
    # Calculate seconds until next minute
    seconds_until_next_minute = 60 - now.second
    
    return {
        "allowed": allowed,
        "limit": RATE_LIMIT,
        "remaining": remaining,
        "current": current,
        "retry_after": seconds_until_next_minute,
    }


def rate_limit_dependency(request: Request):
    """Dependency that enforces rate limiting"""
    user_id = request.client.host
    rate_limit_info = check_rate_limit(user_id)
    
    if not rate_limit_info["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(rate_limit_info["retry_after"]) + " seconds"
            }
        )
    
    return rate_limit_info

@app.get("/api/status")
async def get_status(request: Request, rate_limit: dict = Depends(rate_limit_dependency)):
    """Check current rate limit status - this endpoint IS rate limited"""
    user_id = request.client.host
    now = datetime.now()
    current_minute = now.strftime("%Y-%m-%d-%H-%M")
    key = f"rate_limit:{user_id}:{current_minute}"
    
    current = redis_client.get(key)
    current = int(current) if current else 0
    remaining = max(0, RATE_LIMIT - current)
    
    # Calculate seconds until next minute
    seconds_until_reset = 60 - now.second
    
    return {
        "user_id": user_id,
        "limit": RATE_LIMIT,
        "current_requests": current,
        "remaining": remaining,
        "resets_in_seconds": seconds_until_reset
    }


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.ConnectionError:
        return {"status": "unhealthy", "redis": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Rate Limiter Demo...")
    print(f"⚡ Rate limit: {RATE_LIMIT} requests every {WINDOW_SECONDS} seconds")
    print("📚 API docs: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)

