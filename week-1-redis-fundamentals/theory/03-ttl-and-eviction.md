# TTL and Eviction Policies

## Time To Live (TTL)

TTL determines how long a key stays in Redis before it's automatically deleted. This is **crucial** for caching!

### Why TTL Matters

1. **Memory Management**: Prevent Redis from filling up with old data
2. **Data Freshness**: Ensure cached data doesn't become too stale
3. **Cost Control**: Keep memory usage (and costs) under control

### Setting TTL

```bash
# Set with initial value
SET cache:user:1000 "data" EX 3600  # Expires in 1 hour
SET cache:user:1000 "data" PX 60000 # Expires in 60,000 milliseconds

# Set on existing key
EXPIRE cache:user:1000 3600  # Set to 3600 seconds
PEXPIRE cache:user:1000 60000  # Set to milliseconds

# Set expiration at specific timestamp
EXPIREAT cache:user:1000 1700000000  # Unix timestamp

# Check TTL
TTL cache:user:1000
# Returns: seconds remaining, -1 = no expiration, -2 = key doesn't exist

# Remove expiration
PERSIST cache:user:1000
```

### TTL Strategy by Use Case

| Use Case | Recommended TTL | Reasoning |
|----------|----------------|-----------|
| User session | 15-30 minutes | Balance UX and security |
| API response cache | 5-60 minutes | Depends on data change frequency |
| Database query cache | 5-15 minutes | Keep data reasonably fresh |
| Static content (CDN) | 1-24 hours | Rarely changes |
| Rate limiting | 1 second - 1 hour | Depends on rate limit window |
| Temporary tokens | 5-15 minutes | Security-sensitive |
| Product catalog | 1-6 hours | Changes infrequently |
| Real-time data | 10-60 seconds | Needs to be very fresh |

### Python TTL Examples

```python
import redis
from datetime import timedelta

r = redis.Redis(decode_responses=True)

# Example 1: Cache API response
def cache_api_response(endpoint, data, ttl_minutes=10):
    key = f"api:cache:{endpoint}"
    r.setex(key, timedelta(minutes=ttl_minutes), data)
    
# Example 2: Session with sliding expiration
def refresh_session(session_id):
    key = f"session:{session_id}"
    if r.exists(key):
        # Extend session by 30 minutes on each request
        r.expire(key, timedelta(minutes=30))
        return True
    return False

# Example 3: Check if cache is stale
def get_with_ttl_check(key, min_ttl_seconds=300):
    """Only return cached data if it has at least 5 minutes left"""
    ttl = r.ttl(key)
    if ttl > min_ttl_seconds:
        return r.get(key)
    return None  # Cache too stale, refresh it
```

---

## Eviction Policies

What happens when Redis runs out of memory? **Eviction policies** decide which keys to remove.

### Configuring Max Memory

```bash
# In redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

Or via CLI:
```bash
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru
```

### Available Eviction Policies

#### 1. **noeviction** (Default)
- **Behavior**: Return errors when memory limit is reached
- **Use case**: When you want explicit control; not recommended for caching

```bash
CONFIG SET maxmemory-policy noeviction
```

#### 2. **allkeys-lru** ⭐ (Recommended for most caches)
- **Behavior**: Evict least recently used keys among ALL keys
- **Use case**: General-purpose caching
- **Best for**: When all keys are cache data

```bash
CONFIG SET maxmemory-policy allkeys-lru
```

#### 3. **volatile-lru**
- **Behavior**: Evict LRU keys among keys with TTL set
- **Use case**: Mix of cached data (with TTL) and persistent data (no TTL)
- **Best for**: When some keys must never be evicted

```bash
CONFIG SET maxmemory-policy volatile-lru
```

#### 4. **allkeys-lfu** (Least Frequently Used)
- **Behavior**: Evict least frequently used keys
- **Use case**: When access frequency matters more than recency
- **Best for**: Detecting "one-time" vs "popular" keys

```bash
CONFIG SET maxmemory-policy allkeys-lfu
```

#### 5. **volatile-lfu**
- **Behavior**: Evict LFU keys among keys with TTL
- **Use case**: Mix of data types, evict by frequency

#### 6. **allkeys-random**
- **Behavior**: Evict random keys
- **Use case**: When access patterns are uniform

#### 7. **volatile-random**
- **Behavior**: Evict random keys among keys with TTL

#### 8. **volatile-ttl**
- **Behavior**: Evict keys with shortest TTL first
- **Use case**: Prioritize keeping "fresher" cache data

### Policy Comparison

```python
"""
Example: 1000 keys in Redis, 100MB max memory, all used up

allkeys-lru:
- Evicts: Key accessed 1 day ago
- Keeps: Key accessed 1 minute ago
- Best for: Typical caching scenarios

allkeys-lfu:
- Evicts: Key accessed once
- Keeps: Key accessed 1000 times
- Best for: Detecting popular content

volatile-ttl:
- Evicts: Key with TTL of 10 seconds
- Keeps: Key with TTL of 1 hour
- Best for: Prioritizing "fresh" data
"""
```

---

## LRU vs LFU: When to Use Each

### LRU (Least Recently Used) - Most Common ⭐

**How it works**: Tracks when keys were last accessed

**Example:**
```
Keys: A (accessed 1 min ago), B (5 min ago), C (10 min ago)
Memory full → Evicts C (oldest access)
```

**Best for:**
- General web caching
- API response caching
- User session data
- Recent activity matters more than total activity

### LFU (Least Frequently Used)

**How it works**: Tracks how many times keys were accessed

**Example:**
```
Keys: A (accessed 100 times), B (accessed 10 times), C (accessed 5 times)
Memory full → Evicts C (least popular)
```

**Best for:**
- Content recommendation systems
- Popular product caching
- Analytics data
- Long-running caches where some data is inherently more popular

---

## Cache Invalidation Strategies

"There are only two hard things in Computer Science: cache invalidation and naming things." - Phil Karlton

### 1. TTL-Based (Passive)

**Pros**: Simple, automatic
**Cons**: Data can be stale for TTL duration

```python
# Set and forget
r.setex('user:1000:profile', 3600, user_data)
```

### 2. Explicit Invalidation (Active)

**Pros**: Immediate consistency
**Cons**: Must remember to invalidate everywhere

```python
def update_user_profile(user_id, new_data):
    # 1. Update database
    db.update('users', user_id, new_data)
    
    # 2. Invalidate cache
    r.delete(f'user:{user_id}:profile')
    
    # Or update cache directly
    r.setex(f'user:{user_id}:profile', 3600, new_data)
```

### 3. Cache-Aside with TTL (Best of Both Worlds)

```python
def get_user_profile(user_id):
    key = f'user:{user_id}:profile'
    
    # Try cache
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    
    # Cache miss - query DB
    data = db.query('SELECT * FROM users WHERE id = ?', user_id)
    
    # Store with TTL
    r.setex(key, 3600, json.dumps(data))
    
    return data

def update_user_profile(user_id, new_data):
    # Update DB
    db.update('users', user_id, new_data)
    
    # Invalidate cache (will be refreshed on next read)
    r.delete(f'user:{user_id}:profile')
```

### 4. Probabilistic Early Expiration

Prevents cache stampedes by refreshing cache before expiration.

```python
import random
import time

def get_cached_data(key, fetch_function, ttl=3600):
    data = r.get(key)
    
    if data:
        # Check if we should refresh early
        remaining_ttl = r.ttl(key)
        
        # If TTL < 10% of original, maybe refresh
        if remaining_ttl < ttl * 0.1:
            if random.random() < 0.1:  # 10% chance
                # Refresh cache in background
                new_data = fetch_function()
                r.setex(key, ttl, new_data)
        
        return data
    
    # Cache miss
    new_data = fetch_function()
    r.setex(key, ttl, new_data)
    return new_data
```

---

## Monitoring TTL and Evictions

```python
import redis

r = redis.Redis(decode_responses=True)

# Get memory info
info = r.info('memory')
print(f"Used Memory: {info['used_memory_human']}")
print(f"Max Memory: {info['maxmemory_human']}")

# Get stats
stats = r.info('stats')
print(f"Evicted Keys: {stats['evicted_keys']}")
print(f"Expired Keys: {stats['expired_keys']}")

# Get keyspace info
keyspace = r.info('keyspace')
print(keyspace)

# Check specific key TTL
ttl = r.ttl('user:1000:profile')
if ttl > 0:
    print(f"Key expires in {ttl} seconds")
elif ttl == -1:
    print("Key has no expiration")
else:
    print("Key doesn't exist")
```

---

## Best Practices

### 1. Always Set TTL for Cache Keys ⭐
```python
# ❌ Bad - no expiration
r.set('cache:data', value)

# ✅ Good - with TTL
r.setex('cache:data', 3600, value)
```

### 2. Use Shorter TTL for Frequently Changing Data
```python
# User preferences (change often) - 5 minutes
r.setex('user:prefs', 300, data)

# Product catalog (change rarely) - 1 hour
r.setex('product:catalog', 3600, data)
```

### 3. Monitor Eviction Rates
```python
# High eviction rate = need more memory or shorter TTLs
if stats['evicted_keys'] > 1000:
    print("Warning: High eviction rate!")
```

### 4. Choose Right Eviction Policy
```python
# For pure caching: allkeys-lru
# For mixed workload: volatile-lru
# For popularity-based: allkeys-lfu
```

---

## 🎯 Key Takeaways

1. **Always set TTL** for cache keys to prevent memory bloat
2. **Choose appropriate TTL** based on data change frequency
3. **allkeys-lru** is best for most caching scenarios
4. **Monitor eviction rates** to optimize memory usage
5. **Combine TTL with explicit invalidation** for best results
6. **Use probabilistic early expiration** to prevent cache stampedes

---

**Next**: [Use Cases for Backend Engineers](./04-use-cases.md)

