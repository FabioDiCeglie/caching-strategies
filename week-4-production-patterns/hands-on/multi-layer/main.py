"""
Multi-Layer Caching Demo

Two cache layers:
- L1: In-memory (fast, per-instance, small)
- L2: Redis (shared, larger, network hop)

Endpoints:
- /product/redis-only   → L2 only
- /product/multi-layer  → L1 + L2
"""

import os
import time
import json
import redis
from cachetools import TTLCache
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Multi-Layer Cache Demo")

# Redis connection (L2)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# In-memory cache (L1) - 100 items max, 5 second TTL
l1_cache = TTLCache(maxsize=100, ttl=5)

# Stats tracking
stats = {
    "l1_hits": 0,
    "l2_hits": 0,
    "db_hits": 0
}


def expensive_db_query(product_id: int):
    """Simulates slow database query"""
    time.sleep(0.5)  # 500ms delay
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": 99.99,
        "fetched_at": time.strftime("%H:%M:%S")
    }


# ============================================================
# L2 Only: Redis cache
# ============================================================
@app.get("/product/redis-only/{product_id}")
def get_product_redis_only(product_id: int):
    """
    Single layer: Redis only
    Every request = 1 network call to Redis
    """
    cache_key = f"product:{product_id}"
    
    # Check Redis (L2)
    cached = redis_client.get(cache_key)
    if cached:
        stats["l2_hits"] += 1
        return {"source": "L2 (Redis)", "data": json.loads(cached)}
    
    # Cache miss - query DB
    stats["db_hits"] += 1
    data = expensive_db_query(product_id)
    redis_client.set(cache_key, json.dumps(data), ex=60)
    
    return {"source": "database", "data": data}


# ============================================================
# Multi-Layer: L1 (memory) + L2 (Redis)
# ============================================================
@app.get("/product/multi-layer/{product_id}")
def get_product_multi_layer(product_id: int):
    """
    Two layers: Memory → Redis → Database
    Most requests avoid network call entirely
    """
    cache_key = f"product:{product_id}"
    
    # Check L1 (in-memory) - no network!
    if cache_key in l1_cache:
        stats["l1_hits"] += 1
        return {"source": "L1 (Memory)", "data": l1_cache[cache_key]}
    
    # Check L2 (Redis)
    cached = redis_client.get(cache_key)
    if cached:
        stats["l2_hits"] += 1
        data = json.loads(cached)
        l1_cache[cache_key] = data  # Populate L1
        return {"source": "L2 (Redis)", "data": data}
    
    # Cache miss - query DB
    stats["db_hits"] += 1
    data = expensive_db_query(product_id)
    
    # Cache in both layers
    redis_client.set(cache_key, json.dumps(data), ex=60)
    l1_cache[cache_key] = data
    
    return {"source": "database", "data": data}


# ============================================================
# Utility endpoints
# ============================================================
@app.get("/stats")
def get_stats():
    """View cache hit statistics"""
    total = stats["l1_hits"] + stats["l2_hits"] + stats["db_hits"]
    return {
        "l1_hits": stats["l1_hits"],
        "l2_hits": stats["l2_hits"],
        "db_hits": stats["db_hits"],
        "total_requests": total,
        "l1_hit_rate": f"{(stats['l1_hits']/total*100):.1f}%" if total > 0 else "0%"
    }


@app.delete("/cache")
def clear_cache():
    """Clear all caches and reset stats"""
    l1_cache.clear()
    redis_client.flushdb()
    stats["l1_hits"] = 0
    stats["l2_hits"] = 0
    stats["db_hits"] = 0
    return {"message": "All caches cleared"}


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Multi-Layer Cache Demo</title>
        <style>
            body { font-family: system-ui; max-width: 900px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .layers { display: flex; gap: 20px; margin: 30px 0; }
            .layer { flex: 1; padding: 20px; border-radius: 8px; text-align: center; }
            .l1 { background: #e8f5e9; border: 2px solid #4caf50; }
            .l2 { background: #e3f2fd; border: 2px solid #2196f3; }
            .db { background: #fff3e0; border: 2px solid #ff9800; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; font-size: 14px; border: none; border-radius: 4px; }
            .green { background: #4caf50; color: white; }
            .blue { background: #2196f3; color: white; }
            .orange { background: #ff9800; color: white; }
            pre { background: #1e1e1e; color: #ddd; padding: 15px; border-radius: 4px; }
            #result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🏗️ Multi-Layer Cache Demo</h1>
        
        <div class="layers">
            <div class="layer l1">
                <h3>L1: Memory</h3>
                <p>~0.001ms</p>
                <p>Per instance</p>
                <p>TTL: 5s</p>
            </div>
            <div class="layer l2">
                <h3>L2: Redis</h3>
                <p>~1-5ms</p>
                <p>Shared</p>
                <p>TTL: 60s</p>
            </div>
            <div class="layer db">
                <h3>Database</h3>
                <p>~500ms</p>
                <p>Origin</p>
            </div>
        </div>
        
        <h3>Test Endpoints</h3>
        <p>
            <button class="blue" onclick="testEndpoint('/product/redis-only/1')">Redis Only</button>
            <button class="green" onclick="testEndpoint('/product/multi-layer/1')">Multi-Layer</button>
            <button class="orange" onclick="clearCache()">Clear Cache</button>
            <button onclick="showStats()">Show Stats</button>
        </p>
        
        <div id="result"></div>
        
        <h3>How It Works</h3>
        <pre>
Redis Only:
  Request → Redis → (miss?) → Database
  Every request = network call

Multi-Layer:
  Request → Memory → (miss?) → Redis → (miss?) → Database
  Most requests = no network call!
        </pre>
        
        <script>
            async function testEndpoint(url) {
                const start = performance.now();
                const res = await fetch(url);
                const data = await res.json();
                const time = (performance.now() - start).toFixed(2);
                document.getElementById('result').innerHTML = 
                    '<strong>Source:</strong> ' + data.source + '<br>' +
                    '<strong>Time:</strong> ' + time + 'ms<br>' +
                    '<strong>Data:</strong> ' + JSON.stringify(data.data);
            }
            
            async function clearCache() {
                await fetch('/cache', {method: 'DELETE'});
                document.getElementById('result').innerHTML = 'Cache cleared!';
            }
            
            async function showStats() {
                const res = await fetch('/stats');
                const data = await res.json();
                document.getElementById('result').innerHTML = 
                    '<strong>L1 Hits:</strong> ' + data.l1_hits + '<br>' +
                    '<strong>L2 Hits:</strong> ' + data.l2_hits + '<br>' +
                    '<strong>DB Hits:</strong> ' + data.db_hits + '<br>' +
                    '<strong>L1 Hit Rate:</strong> ' + data.l1_hit_rate;
            }
        </script>
    </body>
    </html>
    """

