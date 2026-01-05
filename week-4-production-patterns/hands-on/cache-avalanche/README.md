# Cache Avalanche Demo

Demonstrates the cache avalanche problem and how jittered TTLs solve it.

## Quick Start

```bash
chmod +x start.sh stop.sh
./start.sh
```

Open: http://localhost:8006

## The Problem

All cache entries expire at the same time → massive DB spike.

```
T=0:      Cache 100 products with TTL=10s
T=10:     ALL 100 expire at once!
          → 100 DB queries simultaneously 💥
```

## The Solution

Add random jitter to TTLs → spread out expiration.

```
T=0:      Cache 100 products with TTL=10s ± 3s
T=7-13:   Products expire gradually over 6 seconds
          → ~15 DB queries spread out ✅
```

## Test It

```bash
docker exec -it cache-avalanche-api python test_avalanche.py
```

## Expected Output

```
NO JITTER:   50 DB queries (all at once) 💥
WITH JITTER: 15 DB queries (spread out) ✅

⚡ Jitter reduced DB spike by 70%!
```

## How It Works

```python
# Without jitter - all same TTL
redis.set(key, data, ex=60)

# With jitter - random TTL
jitter = random.randint(-6, 6)  # ±10%
redis.set(key, data, ex=60 + jitter)
```

## Stop

```bash
./stop.sh
```

