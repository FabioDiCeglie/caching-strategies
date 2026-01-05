"""
Cache Avalanche Demo

The Problem:
- Many cache entries expire at the same time
- All requests hit database simultaneously

The Solution:
- Add random jitter to TTLs
- Spread out expiration times
"""

import os
import time
import json
import random
import redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Cache Avalanche Demo")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Stats
stats = {"db_queries": 0}

# Base TTL: 10 seconds (short for demo)
BASE_TTL = 10


def query_database(product_id: int):
    """Simulates database query"""
    stats["db_queries"] += 1
    time.sleep(0.1)  # 100ms query time
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": round(random.uniform(10, 100), 2)
    }


# ============================================================
# WITHOUT JITTER: All expire at same time
# ============================================================
@app.post("/warm/no-jitter")
def warm_cache_no_jitter(count: int = 100):
    """
    Warm cache WITHOUT jitter.
    All items get same TTL → expire together → avalanche!
    """
    stats["db_queries"] = 0
    
    for i in range(1, count + 1):
        data = query_database(i)
        key = f"product:no-jitter:{i}"
        redis_client.set(key, json.dumps(data), ex=BASE_TTL)
    
    return {
        "message": f"Cached {count} products with TTL={BASE_TTL}s (no jitter)",
        "all_expire_at": "same time!"
    }


@app.get("/product/no-jitter/{product_id}")
def get_product_no_jitter(product_id: int):
    """Get product (no jitter cache)"""
    key = f"product:no-jitter:{product_id}"
    
    cached = redis_client.get(key)
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    
    print(f"❌ MISS product:{product_id}")
    data = query_database(product_id)
    redis_client.set(key, json.dumps(data), ex=BASE_TTL)
    return {"source": "database", "data": data}


# ============================================================
# WITH JITTER: Spread out expiration
# ============================================================
@app.post("/warm/with-jitter")
def warm_cache_with_jitter(count: int = 100):
    """
    Warm cache WITH jitter.
    Items get random TTL → expire gradually → no avalanche!
    """
    stats["db_queries"] = 0
    ttls = []
    
    for i in range(1, count + 1):
        data = query_database(i)
        key = f"product:with-jitter:{i}"
        
        # Add ±30% jitter
        jitter = random.randint(-3, 3)  # ±3 seconds on 10s base
        ttl = BASE_TTL + jitter
        ttls.append(ttl)
        
        redis_client.set(key, json.dumps(data), ex=ttl)
    
    return {
        "message": f"Cached {count} products with TTL={BASE_TTL}s ± 3s jitter",
        "ttl_range": f"{min(ttls)}s - {max(ttls)}s",
        "spread": "6 second window"
    }


@app.get("/product/with-jitter/{product_id}")
def get_product_with_jitter(product_id: int):
    """Get product (jittered cache)"""
    key = f"product:with-jitter:{product_id}"
    
    cached = redis_client.get(key)
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    
    print(f"❌ MISS product:{product_id}")
    data = query_database(product_id)
    
    # Add jitter on refetch too
    jitter = random.randint(-3, 3)
    ttl = BASE_TTL + jitter
    
    redis_client.set(key, json.dumps(data), ex=ttl)
    return {"source": "database", "data": data}


# ============================================================
# Utility endpoints
# ============================================================
@app.get("/ttls")
def check_ttls():
    """Check remaining TTLs for cached products"""
    no_jitter_ttls = []
    with_jitter_ttls = []
    
    for i in range(1, 101):
        ttl = redis_client.ttl(f"product:no-jitter:{i}")
        if ttl > 0:
            no_jitter_ttls.append(ttl)
        
        ttl = redis_client.ttl(f"product:with-jitter:{i}")
        if ttl > 0:
            with_jitter_ttls.append(ttl)
    
    return {
        "no_jitter": {
            "count": len(no_jitter_ttls),
            "ttls": no_jitter_ttls[:10] if no_jitter_ttls else [],
            "all_same": len(set(no_jitter_ttls)) <= 1 if no_jitter_ttls else None
        },
        "with_jitter": {
            "count": len(with_jitter_ttls),
            "ttls": with_jitter_ttls[:10] if with_jitter_ttls else [],
            "spread": f"{min(with_jitter_ttls)}-{max(with_jitter_ttls)}s" if with_jitter_ttls else None
        }
    }


@app.delete("/cache")
def clear_cache():
    """Clear all cache"""
    redis_client.flushdb()
    stats["db_queries"] = 0
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
        <title>Cache Avalanche Demo</title>
        <style>
            body { font-family: system-ui; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            pre { background: #1e1e1e; color: #ddd; padding: 15px; border-radius: 4px; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🌊 Cache Avalanche Demo</h1>
        
        <h3>Run the test:</h3>
        <pre>docker exec -it cache-avalanche-api python test_avalanche.py</pre>
        
        <h3>The Problem</h3>
        <p>All cache entries expire at the same time → massive DB spike</p>
        
        <h3>The Solution</h3>
        <p>Add random jitter to TTLs → spread out expiration</p>
        
        <h3>Expected Results</h3>
        <pre>
NO JITTER:   100 items expire → 100 DB queries at once 💥
WITH JITTER: 100 items expire → ~15 DB queries spread over 6 seconds ✅
        </pre>
    </body>
    </html>
    """

