# Solutions to Caching Problems

Practical solutions for the problems we discussed.

---

## 1. Solving Thundering Herd

### Solution A: Locking (Mutex)

Only **one request** regenerates the cache, others wait.

```python
def get_product_with_lock(product_id):
    # Try cache first
    data = cache.get(f"product:{product_id}")
    if data:
        return data
    
    # Try to acquire lock
    lock_key = f"lock:product:{product_id}"
    if cache.set(lock_key, "1", nx=True, ex=5):  # Lock for 5 seconds
        try:
            # Winner: fetch from DB and cache
            data = db.get_product(product_id)
            cache.set(f"product:{product_id}", data, ex=3600)
            return data
        finally:
            cache.delete(lock_key)
    else:
        # Loser: wait and retry
        time.sleep(0.1)
        return get_product_with_lock(product_id)  # Retry
```

```
Timeline with locking:
─────────────────────────────────────────────────────────
T=0.001  Request A → MISS → Acquires lock → Query DB
T=0.002  Request B → MISS → Lock exists → Wait...
T=0.003  Request C → MISS → Lock exists → Wait...
T=0.050  Request A → Caches result, releases lock
T=0.051  Request B → Cache HIT ✅
T=0.052  Request C → Cache HIT ✅
─────────────────────────────────────────────────────────
Result: 1 DB query instead of 100!
```

### Solution B: Stale-While-Revalidate

Serve stale data while refreshing in background.

```python
def get_product_swr(product_id):
    key = f"product:{product_id}"
    data = cache.get(key)
    
    if data:
        # Check if stale (past soft expiry)
        if data['cached_at'] < time.time() - 3000:  # 50 min soft TTL
            # Trigger background refresh
            refresh_in_background(product_id)
        return data['value']  # Return stale data immediately
    
    # Hard miss - must fetch
    return fetch_and_cache(product_id)
```

```
Timeline:
─────────────────────────────────────────────────────────
TTL: 3600s (hard), Soft TTL: 3000s

T=0:     Cache set
T=3000:  Data is "stale" but still valid
T=3001:  Request → Return stale + trigger background refresh
T=3002:  Background: Fetch new data, update cache
T=3003:  Next request → Fresh data
T=3600:  Hard expiry (never reached if refreshed)
─────────────────────────────────────────────────────────
```

---

## 2. Solving Hot Keys

### Solution A: Local Cache (L1 + L2)

Add in-memory cache before Redis.

```python
from cachetools import TTLCache

# L1: In-memory (per instance)
local_cache = TTLCache(maxsize=1000, ttl=10)  # 10 second TTL

def get_product(product_id):
    key = f"product:{product_id}"
    
    # L1: Check local memory first
    if key in local_cache:
        return local_cache[key]
    
    # L2: Check Redis
    data = redis.get(key)
    if data:
        local_cache[key] = data  # Populate L1
        return data
    
    # Miss: Fetch from DB
    data = db.get_product(product_id)
    redis.set(key, data, ex=3600)
    local_cache[key] = data
    return data
```

```
Benefits:
─────────────────────────────────────────────────────────
Without L1:  1M requests → 1M Redis calls
With L1:     1M requests → ~100K Redis calls (90% L1 hits)
─────────────────────────────────────────────────────────
```

### Solution B: Key Replication

Spread hot key across multiple keys.

```python
import random

def get_hot_product(product_id):
    # Spread across 10 replica keys
    replica = random.randint(0, 9)
    key = f"product:{product_id}:replica:{replica}"
    
    data = redis.get(key)
    if data:
        return data
    
    # Fetch and cache to ALL replicas
    data = db.get_product(product_id)
    for i in range(10):
        redis.set(f"product:{product_id}:replica:{i}", data, ex=3600)
    return data
```

---

## 3. Solving Cache Avalanche

### Solution: Jittered TTLs

Add randomness to prevent simultaneous expiration.

```python
import random

def cache_with_jitter(key, data, base_ttl=3600):
    # Add ±10% jitter
    jitter = random.randint(-360, 360)  # ±10%
    ttl = base_ttl + jitter
    redis.set(key, data, ex=ttl)
```

```
Without jitter:
─────────────────────────────────────────────────────────
product:1  expires at T=3600
product:2  expires at T=3600
product:3  expires at T=3600
...
All expire together! 💥

With jitter:
─────────────────────────────────────────────────────────
product:1  expires at T=3542
product:2  expires at T=3687
product:3  expires at T=3601
...
Spread out over 720 seconds ✅
```

---

## 4. Solving Cache Penetration

### Solution A: Negative Caching

Cache "not found" results too.

```python
def get_user(user_id):
    key = f"user:{user_id}"
    
    cached = redis.get(key)
    if cached == "NULL":
        return None  # Known to not exist
    if cached:
        return cached
    
    # Fetch from DB
    user = db.get_user(user_id)
    
    if user:
        redis.set(key, user, ex=3600)
    else:
        # Cache the "not found" with shorter TTL
        redis.set(key, "NULL", ex=300)  # 5 minutes
    
    return user
```

### Solution B: Bloom Filter

Probabilistic filter to check if key might exist.

```python
from pybloom_live import BloomFilter

# Initialize with known IDs
bloom = BloomFilter(capacity=1000000, error_rate=0.001)
for user_id in db.get_all_user_ids():
    bloom.add(user_id)

def get_user(user_id):
    # Quick check: definitely doesn't exist?
    if user_id not in bloom:
        return None  # 100% certain not in DB
    
    # Might exist - check cache/DB
    return get_user_from_cache_or_db(user_id)
```

---

## 5. Cache Warming

Pre-populate cache before traffic hits.

```python
def warm_cache():
    """Run on deployment or startup"""
    
    # Get most accessed items
    popular_products = db.get_popular_products(limit=1000)
    
    for product in popular_products:
        key = f"product:{product['id']}"
        # Use jittered TTL to prevent avalanche
        ttl = 3600 + random.randint(-360, 360)
        redis.set(key, product, ex=ttl)
    
    print(f"Warmed {len(popular_products)} products")
```

### When to Warm

```
─────────────────────────────────────────────────────────
✅ After deployment (new instances have cold cache)
✅ After Redis restart
✅ Before expected traffic spike (planned event)
✅ Scheduled job during low traffic
─────────────────────────────────────────────────────────
```

---

## Summary: Solutions Quick Reference

| Problem | Solution | Implementation |
|---------|----------|----------------|
| **Thundering Herd** | Locking / SWR | `SET lock NX EX` |
| **Hot Keys** | L1 cache / Replication | In-memory + Redis |
| **Cache Avalanche** | Jittered TTLs | `TTL + random()` |
| **Cache Penetration** | Negative caching / Bloom filter | Cache "NULL" values |
| **Cold Cache** | Cache warming | Pre-populate on startup |

---

## Production Checklist

```
□ Use locking for expensive/slow queries
□ Add jitter to all TTLs (±10%)
□ Implement negative caching for user-facing lookups
□ Consider L1 cache for hot keys
□ Warm cache after deployments
□ Monitor hit/miss ratios
□ Set up alerts for low hit rates
```

