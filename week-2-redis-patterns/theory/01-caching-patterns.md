# Caching Patterns

## The Three Main Caching Patterns

### 1. Cache-Aside (Lazy Loading) ⭐ Most Common

**How it works:**
```
App → Check cache → Miss → Query DB → Store in cache → Return
App → Check cache → Hit → Return (no DB query)
```

**Implementation:**
```python
def get_user(user_id):
    # Try cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss - query database
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    
    # Store in cache
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user
```

**Pros:**
- ✅ Simple to implement
- ✅ Only caches what's actually requested
- ✅ Cache failure doesn't break app

**Cons:**
- ❌ First request is always slow (cache miss)
- ❌ Cache stampede risk on popular keys
- ❌ Stale data if not invalidated

**Best for:** Read-heavy workloads, unpredictable access patterns

---

### 2. Read-Through

**How it works:**
```
App → Cache (cache handles DB if miss) → Return
```

The cache library automatically loads from DB on miss.

**Implementation:**
```python
# Cache library handles everything
@cache.memoize(expire=3600)
def get_user(user_id):
    return db.query("SELECT * FROM users WHERE id = ?", user_id)
```

**Pros:**
- ✅ Cleaner code (cache logic hidden)
- ✅ Consistent cache management

**Cons:**
- ❌ Requires cache library support
- ❌ Less control over caching logic

**Best for:** When using caching libraries, simpler codebases

---

### 3. Write-Through

**How it works:**
```
App → Write to cache AND database simultaneously → Return
```

**Implementation:**
```python
def update_user(user_id, data):
    # Update database
    db.execute("UPDATE users SET name = ? WHERE id = ?", data['name'], user_id)
    
    # Update cache immediately
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
    
    return data
```

**Pros:**
- ✅ Cache always has latest data
- ✅ No stale reads
- ✅ Read performance stays high

**Cons:**
- ❌ Write latency increases (2 operations)
- ❌ Wasted cache space for rarely-read data
- ❌ More complex error handling

**Best for:** Read-heavy with frequent updates, consistency critical

---

### 4. Write-Behind (Write-Back)

**How it works:**
```
App → Write to cache → Return (fast!)
Background job → Writes to DB later
```

**Implementation:**
```python
def update_user(user_id, data):
    # Write to cache immediately
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
    
    # Queue DB write for later
    queue.enqueue('write_to_db', user_id, data)
    
    return data  # Return immediately
```

**Pros:**
- ✅ Extremely fast writes
- ✅ Reduces database load
- ✅ Can batch DB writes

**Cons:**
- ❌ Risk of data loss if cache fails
- ❌ Complex to implement
- ❌ Eventual consistency issues

**Best for:** Write-heavy workloads, can tolerate data loss

---

## Comparison Table

| Pattern | Read Performance | Write Performance | Consistency | Complexity |
|---------|-----------------|-------------------|-------------|------------|
| Cache-Aside | Fast (after warm) | Fast | Eventual | Low |
| Read-Through | Fast | Fast | Eventual | Low |
| Write-Through | Fast | Slower | Strong | Medium |
| Write-Behind | Fast | Very Fast | Weak | High |

---

## Real-World Usage

**E-commerce Product Catalog:**
- Pattern: Cache-Aside
- Why: Products don't change often, read-heavy

**Social Media Feed:**
- Pattern: Write-Through
- Why: Need latest posts, high read/write

**Analytics Dashboard:**
- Pattern: Cache-Aside with long TTL
- Why: Data can be slightly stale, expensive queries

**Gaming Leaderboard:**
- Pattern: Write-Behind
- Why: Frequent score updates, can batch to DB

---

## Key Takeaways

1. **Cache-Aside** is the default choice - simple and reliable
2. **Write-Through** when consistency matters more than write speed
3. **Write-Behind** only for high-traffic, loss-tolerant scenarios
4. **Read-Through** is just Cache-Aside with library sugar

---

**Next**: [Cache Invalidation Strategies](./02-cache-invalidation.md)

