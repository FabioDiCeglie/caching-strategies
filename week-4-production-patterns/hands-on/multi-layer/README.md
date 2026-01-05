# Multi-Layer Cache Demo

Demonstrates L1 (in-memory) + L2 (Redis) caching for reduced latency.

## Quick Start

```bash
chmod +x start.sh stop.sh
./start.sh
```

Open: http://localhost:8005

## The Layers

```
L1: Memory     →  L2: Redis    →  Database
(~0.001ms)        (~1-5ms)        (~500ms)
per-instance      shared          origin
TTL: 5s           TTL: 60s
```

## Why Multi-Layer?

| Approach | 100 requests | Network calls |
|----------|--------------|---------------|
| Redis only | ~1-5ms each | 100 |
| Multi-layer | ~0.001ms each | ~1-5 |

Most requests hit L1 (memory) → **no network call!**

## Test It

```bash
docker exec -it multi-layer-api python test_layers.py
```

## Expected Output

```
🔵 Redis Only:
  Avg response time: 3.5ms
  Sources: {'L2 (Redis)': 99, 'database': 1}

🟢 Multi-Layer:
  Avg response time: 1.2ms
  Sources: {'L1 (Memory)': 95, 'L2 (Redis)': 4, 'database': 1}

⚡ Multi-layer is 65% faster!
   L1 served 95 requests without network!
```

## How It Works

```python
# Check L1 (memory) - instant, no network
if key in l1_cache:
    return l1_cache[key]

# Check L2 (Redis) - fast, 1 network call
if data := redis.get(key):
    l1_cache[key] = data  # Populate L1
    return data

# Miss - fetch from DB
data = query_db()
redis.set(key, data)
l1_cache[key] = data
return data
```

## Stop

```bash
./stop.sh
```

