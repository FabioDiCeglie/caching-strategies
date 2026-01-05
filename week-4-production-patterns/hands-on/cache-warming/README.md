# Cache Warming Demo

Demonstrates pre-populating cache on startup for faster initial responses.

## Quick Start

```bash
chmod +x start.sh stop.sh
./start.sh
```

Open: http://localhost:8008

## The Problem

After deployment/restart, cache is empty (cold):
```
User 1: GET /product/1 → Cache MISS → DB query (100ms)
User 2: GET /product/2 → Cache MISS → DB query (100ms)
...
First 50 users wait for DB queries 😕
```

## The Solution

Pre-load popular data into cache on startup:
```
App starts → Warm cache with top 50 products
User 1: GET /product/1 → Cache HIT (1ms) ✅
User 2: GET /product/2 → Cache HIT (1ms) ✅
...
All users get fast responses immediately!
```

## Test It

```bash
docker exec -it cache-warming-api python test_warming.py
```

## Expected Output

```
❄️  COLD CACHE
  DB queries:   50
  Total time:   5000ms

🔥 WARM CACHE
  DB queries:   0
  Total time:   50ms

⚡ Warm cache is 100x faster!
```

## How It Works

```python
# On app startup
@asynccontextmanager
async def lifespan(app):
    warm_cache()  # Pre-load popular items
    yield

def warm_cache():
    popular_ids = get_popular_products()  # From analytics
    for product_id in popular_ids:
        data = db.get(product_id)
        redis.set(f"product:{product_id}", data, ttl=300)
```

## When to Warm

- After deployment
- After Redis restart
- Before expected traffic spike
- Scheduled job during low traffic

## Stop

```bash
./stop.sh
```

