"""
Mini-Project 1: Cache a Slow API
Demonstrates caching external API responses with Redis using cache-aside pattern.
"""

from fastapi import FastAPI, HTTPException
import redis
import httpx
import json
import time
from typing import Optional
from pydantic import BaseModel

app = FastAPI(
    title="Slow API Cache Demo",
    description="Demonstrates caching slow external APIs with Redis",
    version="1.0.0"
)

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True,
    socket_connect_timeout=5
)

EXTERNAL_API_BASE = "https://jsonplaceholder.typicode.com"
DEFAULT_TTL = 300


class CacheResponse(BaseModel):
    data: dict
    cached: bool
    cache_age_seconds: Optional[int] = None
    response_time_ms: float


@app.get("/")
async def root():
    return {
        "message": "Slow API Cache Demo",
        "endpoints": {
            "/users/{user_id}": "Get user by ID (with cache)",
            "/users/{user_id}/nocache": "Get user by ID (without cache)",
            "/posts/{post_id}": "Get post by ID (with cache)",
            "/cache/clear": "Clear all cached data"
        }
    }


@app.get("/users/{user_id}", response_model=CacheResponse)
async def get_user_cached(user_id: int):
    """Get user data with caching (cache-aside pattern)"""
    start_time = time.time()
    cache_key = f"user:{user_id}"
    
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        ttl = redis_client.ttl(cache_key)
        cache_age = DEFAULT_TTL - ttl
        response_time = (time.time() - start_time) * 1000
        
        return CacheResponse(
            data=json.loads(cached_data),
            cached=True,
            cache_age_seconds=cache_age,
            response_time_ms=round(response_time, 2)
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EXTERNAL_API_BASE}/users/{user_id}",
                timeout=10.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="User not found")
            
            response.raise_for_status()
            data = response.json()
        
        redis_client.setex(cache_key, DEFAULT_TTL, json.dumps(data))
        response_time = (time.time() - start_time) * 1000
        
        return CacheResponse(
            data=data,
            cached=False,
            cache_age_seconds=0,
            response_time_ms=round(response_time, 2)
        )
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"External API error: {str(e)}")


@app.get("/users/{user_id}/nocache")
async def get_user_no_cache(user_id: int):
    """Get user data without caching for performance comparison"""
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EXTERNAL_API_BASE}/users/{user_id}",
                timeout=10.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="User not found")
            
            response.raise_for_status()
            data = response.json()
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "data": data,
            "cached": False,
            "response_time_ms": round(response_time, 2)
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"External API error: {str(e)}")


@app.get("/posts/{post_id}", response_model=CacheResponse)
async def get_post_cached(post_id: int, ttl: int = 60):
    """Get post data with custom TTL"""
    start_time = time.time()
    cache_key = f"post:{post_id}"
    
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        ttl_remaining = redis_client.ttl(cache_key)
        cache_age = ttl - ttl_remaining
        response_time = (time.time() - start_time) * 1000
        
        return CacheResponse(
            data=json.loads(cached_data),
            cached=True,
            cache_age_seconds=cache_age,
            response_time_ms=round(response_time, 2)
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{EXTERNAL_API_BASE}/posts/{post_id}",
                timeout=10.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Post not found")
            
            response.raise_for_status()
            data = response.json()
        
        redis_client.setex(cache_key, ttl, json.dumps(data))
        response_time = (time.time() - start_time) * 1000
        
        return CacheResponse(
            data=data,
            cached=False,
            cache_age_seconds=0,
            response_time_ms=round(response_time, 2)
        )
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"External API error: {str(e)}")


@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached data"""
    keys = redis_client.keys("user:*") + redis_client.keys("post:*")
    
    if keys:
        redis_client.delete(*keys)
    
    return {
        "message": "Cache cleared successfully",
        "keys_deleted": len(keys)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        redis_status = "healthy"
    except redis.ConnectionError:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "redis": redis_status
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Slow API Cache Demo...")
    print("📚 API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

