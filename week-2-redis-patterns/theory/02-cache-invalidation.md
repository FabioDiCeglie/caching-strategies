# Cache Invalidation Strategies

> "There are only two hard things in Computer Science: cache invalidation and naming things." - Phil Karlton

## The Problem

```python
# User updates their profile
db.execute("UPDATE users SET name = 'Bob' WHERE id = 1")

# But cache still has old data!
redis.get("user:1")  # Returns: {"name": "Alice"} ❌ STALE!
```

---

## Strategy 1: TTL (Time To Live) ⏰

**Concept:** Let cache expire automatically

```python
# Cache for 5 minutes
redis.setex("user:1", 300, json.dumps(user))

# After 5 minutes: automatic deletion
# Next request: cache miss → fetch fresh data
```

**Pros:**
- ✅ Simple - set and forget
- ✅ Automatic cleanup
- ✅ Works for all data types

**Cons:**
- ❌ Data can be stale for TTL duration
- ❌ No immediate invalidation
- ❌ Cache stampede risk when expires

**Best for:** Data that changes infrequently, acceptable staleness

**TTL Guidelines:**
```python
User profiles: 30-60 minutes
Product catalog: 1-6 hours
Static content: 24 hours
Session data: 30 minutes
API responses: 5-15 minutes
```

---

## Strategy 2: Explicit Invalidation (Delete on Write)

**Concept:** Delete cache when data changes

```python
def update_user(user_id, data):
    # Update database
    db.execute("UPDATE users SET name = ? WHERE id = ?", data['name'], user_id)
    
    # Invalidate cache
    redis.delete(f"user:{user_id}")
```

**Pros:**
- ✅ Immediate consistency
- ✅ No stale data
- ✅ Simple logic

**Cons:**
- ❌ Must remember to invalidate everywhere
- ❌ Next read is slow (cache miss)
- ❌ Can't handle related data easily

**Best for:** Critical data, simple relationships

---

## Strategy 3: Write-Through (Update on Write)

**Concept:** Update cache when writing

```python
def update_user(user_id, data):
    # Update database
    db.execute("UPDATE users SET name = ? WHERE id = ?", data['name'], user_id)
    
    # Update cache with new data
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
```

**Pros:**
- ✅ Cache always fresh
- ✅ Next read is fast (cache hit)
- ✅ No stampede risk

**Cons:**
- ❌ Writes are slower (2 operations)
- ❌ Cache pollution (unused data)
- ❌ Requires fetching full object

**Best for:** Frequently accessed data, read performance critical

---

## Strategy 4: Event-Based Invalidation

**Concept:** Publish events when data changes

```python
def update_user(user_id, data):
    # Update database
    db.execute("UPDATE users SET name = ? WHERE id = ?", data['name'], user_id)
    
    # Publish event
    redis.publish('user:updates', json.dumps({'user_id': user_id}))

# Subscriber invalidates cache
def on_user_update(message):
    data = json.loads(message)
    redis.delete(f"user:{data['user_id']}")
```

**Pros:**
- ✅ Decoupled services
- ✅ Can invalidate related caches
- ✅ Scales across servers

**Cons:**
- ❌ Complex setup
- ❌ Race conditions possible
- ❌ Event delivery must be reliable

**Best for:** Microservices, distributed systems

---

## Strategy 5: SWR (Stale-While-Revalidate)

**Concept:** Return stale data while refreshing in background

```python
def get_user_swr(user_id):
    cached = redis.get(f"user:{user_id}")
    ttl = redis.ttl(f"user:{user_id}")
    
    # If TTL < 10% of original, refresh in background
    if cached and ttl < 360:  # Less than 6 minutes left
        # Return stale data immediately
        background_task.enqueue('refresh_user_cache', user_id)
        return json.loads(cached)
    
    if cached:
        return json.loads(cached)
    
    # Cache miss - fetch and cache
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))
    return user
```

**Pros:**
- ✅ Always fast (return cached)
- ✅ No stampede
- ✅ Gradual refresh

**Cons:**
- ❌ Users might see stale data
- ❌ Background worker needed
- ❌ Complex logic

**Best for:** High-traffic, staleness acceptable

---

## Strategy 6: Cache Tags/Groups

**Concept:** Tag related cache entries for bulk invalidation

```python
# Cache with tags
def cache_user_with_tags(user_id, data):
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
    redis.sadd(f"tag:company:{data['company_id']}", f"user:{user_id}")

# Invalidate all users in a company
def invalidate_company(company_id):
    keys = redis.smembers(f"tag:company:{company_id}")
    if keys:
        redis.delete(*keys)
    redis.delete(f"tag:company:{company_id}")
```

**Pros:**
- ✅ Invalidate related data easily
- ✅ Flexible grouping
- ✅ One operation clears many

**Cons:**
- ❌ Extra storage for tags
- ❌ More complex
- ❌ Must maintain tag relationships

**Best for:** Complex data relationships

---

## Comparison

| Strategy | Consistency | Performance | Complexity | Stale Data Risk |
|----------|-------------|-------------|------------|-----------------|
| TTL | Eventual | High | Low | High |
| Explicit Delete | Strong | Medium | Low | None |
| Write-Through | Strong | Medium | Medium | None |
| Event-Based | Eventual | High | High | Low |
| SWR | Eventual | Very High | High | Medium |
| Cache Tags | Strong | Medium | High | None |

---

## Combining Strategies (Recommended)

Most production systems use **multiple strategies**:

```python
def update_user(user_id, data):
    # Update database
    db.execute("UPDATE users SET name = ? WHERE id = ?", data['name'], user_id)
    
    # Strategy 1: Update cache (Write-Through)
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
    
    # Strategy 2: Publish event (Event-Based)
    redis.publish('user:updates', json.dumps({'user_id': user_id}))
    
    # Strategy 3: Still set TTL as safety net (TTL)
    # Already done in setex above
```

---

## Best Practices

1. **Always set TTL** - Even if you invalidate explicitly, TTL is a safety net
2. **Monitor stale rate** - Track how often users see stale data
3. **Use tags for related data** - Company → Users, Category → Products
4. **Combine strategies** - TTL + Explicit invalidation is common
5. **Test invalidation** - Ensure it works across all code paths

---

## Common Pitfalls

❌ **Forgetting to invalidate in one place**
```python
# Updated here
update_user(user_id, data)  # ✅ Invalidates

# But forgot here
admin_update_user(user_id, data)  # ❌ No invalidation
```

❌ **Invalidating too early**
```python
redis.delete(f"user:{user_id}")
db.execute("UPDATE ...")  # ❌ If this fails, cache is gone but DB unchanged
```

❌ **Not invalidating related data**
```python
# Update user's company
update_user_company(user_id, new_company_id)
redis.delete(f"user:{user_id}")  # ✅ User cache cleared
# ❌ But company user list still has old data!
```

---

## Key Takeaways

1. **TTL** is your safety net - always use it
2. **Explicit invalidation** for critical data
3. **Write-Through** for high-read, low-write
4. **SWR** for high-traffic, staleness ok
5. **Combine strategies** for production

---

**Next**: [Distributed Locks with Redis](./03-distributed-locks.md)

