"""
Cache Warming Demo

The Problem:
- After deployment/restart, cache is empty (cold)
- First users experience slow responses

The Solution:
- Pre-populate cache with popular data on startup
- First users get fast responses immediately
"""

import os
import time
import json
import random
import redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Simulated database
def query_database(product_id: int):
    """Simulates slow database query"""
    time.sleep(0.1)  # 100ms
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": round(random.uniform(10, 100), 2),
        "category": random.choice(["Electronics", "Clothing", "Books", "Home"])
    }


def get_popular_products():
    """Simulates getting list of popular product IDs from analytics"""
    # In reality: query analytics DB or read from config
    return list(range(1, 51))  # Top 50 products


# ============================================================
# Cache Warming Function
# ============================================================
def warm_cache():
    """Pre-populate cache with popular products"""
    print("\n🔥 WARMING CACHE...")
    
    popular_ids = get_popular_products()
    warmed = 0
    
    for product_id in popular_ids:
        key = f"product:{product_id}"
        
        # Skip if already cached
        if redis_client.exists(key):
            continue
        
        # Fetch from DB and cache
        data = query_database(product_id)
        
        # Add jitter to TTL (avoid avalanche)
        ttl = 300 + random.randint(-30, 30)
        redis_client.set(key, json.dumps(data), ex=ttl)
        warmed += 1
    
    print(f"✅ CACHE WARMED: {warmed} products pre-loaded")
    return warmed


# ============================================================
# Lifespan: Warm cache on startup
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm the cache
    warm_cache()
    yield
    # Shutdown: nothing needed


app = FastAPI(title="Cache Warming Demo", lifespan=lifespan)


# ============================================================
# Endpoints
# ============================================================
@app.get("/product/{product_id}")
def get_product(product_id: int):
    """Get product - should be fast if cache is warm"""
    key = f"product:{product_id}"
    
    start = time.time()
    
    # Check cache
    cached = redis_client.get(key)
    if cached:
        duration = (time.time() - start) * 1000
        return {
            "source": "cache",
            "duration_ms": round(duration, 2),
            "data": json.loads(cached)
        }
    
    # Cache miss - query DB
    data = query_database(product_id)
    
    ttl = 300 + random.randint(-30, 30)
    redis_client.set(key, json.dumps(data), ex=ttl)
    
    duration = (time.time() - start) * 1000
    return {
        "source": "database",
        "duration_ms": round(duration, 2),
        "data": data
    }


@app.post("/warm")
def trigger_warm():
    """Manually trigger cache warming"""
    warmed = warm_cache()
    return {"message": f"Warmed {warmed} products"}


@app.delete("/cache")
def clear_cache():
    """Clear all cache (simulate cold start)"""
    redis_client.flushdb()
    return {"message": "Cache cleared - now cold!"}


@app.get("/stats")
def get_stats():
    """Check how many products are cached"""
    keys = redis_client.keys("product:*")
    return {
        "cached_products": len(keys),
        "popular_products": len(get_popular_products()),
        "coverage": f"{len(keys)}/{len(get_popular_products())}"
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cache Warming Demo</title>
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            pre { background: #1e1e1e; color: #ddd; padding: 15px; border-radius: 4px; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🔥 Cache Warming Demo</h1>
        
        <h3>Run the test:</h3>
        <pre>docker exec -it cache-warming-api python test_warming.py</pre>
        
        <h3>The Problem</h3>
        <p>After restart, cache is empty → first users wait for DB queries</p>
        
        <h3>The Solution</h3>
        <p>Pre-load popular data into cache on startup</p>
        
        <h3>Expected Results</h3>
        <pre>
COLD CACHE:  50 requests → 50 DB queries → ~5000ms total
WARM CACHE:  50 requests → 0 DB queries  → ~50ms total ✅
        </pre>
    </body>
    </html>
    """

