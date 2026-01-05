"""
Thundering Herd Demo

Two endpoints:
1. /product/unsafe   - No protection (causes stampede)
2. /product/safe     - With locking (prevents stampede)
"""

import os
import time
import json
import redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Thundering Herd Demo")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Simulated "expensive" database query
def expensive_db_query():
    """Simulates a slow database query (2 seconds)"""
    print("💾 DATABASE QUERY STARTED...")
    time.sleep(2)  # Simulate slow query
    data = {
        "id": 1,
        "name": "Popular Product",
        "price": 99.99,
        "fetched_at": time.strftime("%H:%M:%S")
    }
    print("💾 DATABASE QUERY COMPLETED")
    return data


# ============================================================
# UNSAFE: No protection - causes thundering herd
# ============================================================
@app.get("/product/unsafe")
def get_product_unsafe():
    """
    No protection against thundering herd.
    Every cache miss triggers a DB query.
    """
    cache_key = "product:1:unsafe"
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        print("✅ CACHE HIT (unsafe)")
        return {"source": "cache", "data": json.loads(cached)}
    
    # Cache miss - query DB (NO LOCK!)
    print("❌ CACHE MISS (unsafe) - querying DB...")
    data = expensive_db_query()
    
    # Cache for 10 seconds
    redis_client.set(cache_key, json.dumps(data), ex=10)
    
    return {"source": "database", "data": data}


# ============================================================
# SAFE: With locking - prevents thundering herd
# ============================================================
@app.get("/product/safe")
def get_product_safe():
    """
    Protected with locking.
    Only one request queries DB, others wait for cache.
    """
    cache_key = "product:1:safe"
    lock_key = "lock:product:1"
    
    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        print("✅ CACHE HIT (safe)")
        return {"source": "cache", "data": json.loads(cached)}
    
    # Try to acquire lock
    lock_acquired = redis_client.set(lock_key, "1", nx=True, ex=5)
    
    if lock_acquired:
        # Winner: we got the lock, query DB
        print("🔒 LOCK ACQUIRED - querying DB...")
        try:
            data = expensive_db_query()
            redis_client.set(cache_key, json.dumps(data), ex=10)
            return {"source": "database", "data": data}
        finally:
            redis_client.delete(lock_key)
    else:
        # Loser: wait for winner to populate cache
        print("⏳ LOCK EXISTS - waiting for cache...")
        for _ in range(30):  # Wait up to 3 seconds
            time.sleep(0.1)
            cached = redis_client.get(cache_key)
            if cached:
                print("✅ CACHE POPULATED - returning cached data")
                return {"source": "cache", "data": json.loads(cached)}
        
        # Fallback: query DB if cache still not populated
        print("⚠️ TIMEOUT - querying DB as fallback")
        data = expensive_db_query()
        return {"source": "database", "data": data}


# ============================================================
# Utility endpoints
# ============================================================
@app.delete("/cache")
def clear_cache():
    """Clear all cache keys"""
    redis_client.delete("product:1:unsafe", "product:1:safe", "lock:product:1")
    return {"message": "Cache cleared"}


@app.get("/stats")
def get_stats():
    """Check cache status"""
    return {
        "unsafe_cached": redis_client.exists("product:1:unsafe"),
        "safe_cached": redis_client.exists("product:1:safe"),
        "lock_exists": redis_client.exists("lock:product:1")
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Thundering Herd Demo</title>
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; font-size: 16px; }
            .danger { background: #ff4444; color: white; border: none; border-radius: 4px; }
            .safe { background: #44aa44; color: white; border: none; border-radius: 4px; }
            .neutral { background: #4444aa; color: white; border: none; border-radius: 4px; }
            pre { background: #1e1e1e; color: #ddd; padding: 15px; border-radius: 4px; overflow-x: auto; }
            .note { background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>🦬 Thundering Herd Demo</h1>
        
        <div class="note">
            <strong>How to test:</strong> Use the test script to send concurrent requests.
            Watch the server logs to see the difference!
        </div>
        
        <div class="endpoint">
            <h3>❌ Unsafe Endpoint (No Protection)</h3>
            <p>Every cache miss triggers a database query.</p>
            <button class="danger" onclick="fetch('/product/unsafe').then(r=>r.json()).then(d=>alert(JSON.stringify(d,null,2)))">
                GET /product/unsafe
            </button>
        </div>
        
        <div class="endpoint">
            <h3>✅ Safe Endpoint (With Locking)</h3>
            <p>Only one request queries DB, others wait for cache.</p>
            <button class="safe" onclick="fetch('/product/safe').then(r=>r.json()).then(d=>alert(JSON.stringify(d,null,2)))">
                GET /product/safe
            </button>
        </div>
        
        <div class="endpoint">
            <h3>🔧 Utilities</h3>
            <button class="neutral" onclick="fetch('/cache',{method:'DELETE'}).then(()=>alert('Cache cleared!'))">
                Clear Cache
            </button>
            <button class="neutral" onclick="fetch('/stats').then(r=>r.json()).then(d=>alert(JSON.stringify(d,null,2)))">
                Check Stats
            </button>
        </div>
        
        <h2>📊 Expected Results</h2>
        <pre>
# 10 concurrent requests to UNSAFE endpoint:
💾 DATABASE QUERY STARTED...   (request 1)
💾 DATABASE QUERY STARTED...   (request 2)
💾 DATABASE QUERY STARTED...   (request 3)
...
= 10 DB queries! 💥

# 10 concurrent requests to SAFE endpoint:
🔒 LOCK ACQUIRED - querying DB...  (request 1 wins)
⏳ LOCK EXISTS - waiting...        (request 2 waits)
⏳ LOCK EXISTS - waiting...        (request 3 waits)
💾 DATABASE QUERY COMPLETED
✅ CACHE POPULATED                 (request 2 gets cache)
✅ CACHE POPULATED                 (request 3 gets cache)
= 1 DB query! ✅
        </pre>
    </body>
    </html>
    """

