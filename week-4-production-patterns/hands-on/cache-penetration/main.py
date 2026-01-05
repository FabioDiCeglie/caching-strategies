"""
Cache Penetration Demo

The Problem:
- Requests for NON-EXISTENT data always miss cache
- Every request hits database (cache bypass attack)

The Solution:
- Negative caching: cache "not found" results too
"""

import os
import time
import json
import redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Cache Penetration Demo")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Simulated database with only IDs 1-100
VALID_IDS = set(range(1, 101))

# Stats
stats = {"db_queries": 0, "cache_hits": 0, "negative_cache_hits": 0}


def query_database(user_id: int):
    """Simulates database query"""
    stats["db_queries"] += 1
    time.sleep(0.05)  # 50ms query
    
    if user_id in VALID_IDS:
        return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
    return None  # Not found


# ============================================================
# WITHOUT PROTECTION: Every non-existent ID hits DB
# ============================================================
@app.get("/user/unsafe/{user_id}")
def get_user_unsafe(user_id: int):
    """
    No negative caching.
    Non-existent IDs ALWAYS hit database!
    """
    cache_key = f"user:unsafe:{user_id}"
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        stats["cache_hits"] += 1
        return {"source": "cache", "data": json.loads(cached)}
    
    # Cache miss - query DB
    user = query_database(user_id)
    
    if user:
        redis_client.set(cache_key, json.dumps(user), ex=300)
        return {"source": "database", "data": user}
    else:
        # NOT FOUND - but we don't cache it!
        # Next request for same ID will hit DB again
        return {"source": "database", "data": None, "message": "User not found"}


# ============================================================
# WITH NEGATIVE CACHING: Cache "not found" too
# ============================================================
@app.get("/user/safe/{user_id}")
def get_user_safe(user_id: int):
    """
    With negative caching.
    Non-existent IDs are cached as "NULL" → no repeated DB hits.
    """
    cache_key = f"user:safe:{user_id}"
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        if cached == "NULL":
            stats["negative_cache_hits"] += 1
            return {"source": "negative_cache", "data": None, "message": "User not found (cached)"}
        stats["cache_hits"] += 1
        return {"source": "cache", "data": json.loads(cached)}
    
    # Cache miss - query DB
    user = query_database(user_id)
    
    if user:
        redis_client.set(cache_key, json.dumps(user), ex=300)
        return {"source": "database", "data": user}
    else:
        # NOT FOUND - cache it with shorter TTL!
        redis_client.set(cache_key, "NULL", ex=60)  # 1 minute for negative
        return {"source": "database", "data": None, "message": "User not found"}


# ============================================================
# Utility endpoints
# ============================================================
@app.delete("/cache")
def clear_cache():
    """Clear all cache and reset stats"""
    redis_client.flushdb()
    stats["db_queries"] = 0
    stats["cache_hits"] = 0
    stats["negative_cache_hits"] = 0
    return {"message": "Cache cleared"}


@app.get("/stats")
def get_stats():
    """Get query stats"""
    return stats


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cache Penetration Demo</title>
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            pre { background: #1e1e1e; color: #ddd; padding: 15px; border-radius: 4px; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🕳️ Cache Penetration Demo</h1>
        
        <h3>Run the test:</h3>
        <pre>docker exec -it cache-penetration-api python test_penetration.py</pre>
        
        <h3>The Problem</h3>
        <p>Requests for non-existent IDs bypass cache → always hit DB</p>
        
        <h3>The Solution</h3>
        <p>Negative caching: cache "NULL" for non-existent IDs</p>
        
        <h3>Valid IDs</h3>
        <p>Only IDs 1-100 exist. IDs like 999, -1, 99999 don't exist.</p>
        
        <h3>Expected Results</h3>
        <pre>
UNSAFE: 100 requests for non-existent IDs → 100 DB queries 💥
SAFE:   100 requests for non-existent IDs → 10 DB queries ✅
        </pre>
    </body>
    </html>
    """

