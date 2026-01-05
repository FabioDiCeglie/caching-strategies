# Caching Problems at Scale

When your app gets traffic, caching introduces new challenges. Let's understand the most common problems.

---

## 1. Thundering Herd (Cache Stampede)

### The Problem

When a cached item expires, **many requests hit the database simultaneously**.

```
Timeline:
─────────────────────────────────────────────────────────
Cache expires at T=0
                    
T=0.001  Request A → Cache MISS → Query DB
T=0.002  Request B → Cache MISS → Query DB
T=0.003  Request C → Cache MISS → Query DB
T=0.004  Request D → Cache MISS → Query DB
...
T=0.010  100 requests all querying DB simultaneously!
─────────────────────────────────────────────────────────
```

### Why It's Dangerous

```
Normal:     1 request  → 1 DB query  → ✅ OK
Stampede:   100 requests → 100 DB queries → 💥 DB overload
```

### Real-World Example

- Popular product page cached for 60 seconds
- 1000 users viewing the page
- Cache expires → 1000 simultaneous DB queries
- Database crashes or slows down significantly

---

## 2. Hot Keys

### The Problem

Some keys get **disproportionately more traffic** than others.

```
Key Distribution:
─────────────────────────────────────────────────────────
product:1      → 1,000,000 requests/min  🔥 HOT
product:2      → 500 requests/min
product:3      → 200 requests/min
product:4-999  → 10 requests/min each
─────────────────────────────────────────────────────────
```

### Why It's Dangerous

- Single Redis node handles all traffic for hot key
- Network bandwidth bottleneck
- If hot key expires → massive thundering herd

### Real-World Examples

- Viral tweet/post
- Flash sale product
- Breaking news article
- Celebrity profile page

---

## 3. Cache Avalanche

### The Problem

**Many cache entries expire at the same time**, causing massive DB load.

```
Scenario: All caches set at startup with TTL=3600
─────────────────────────────────────────────────────────
T=0:      Set product:1, TTL=3600
T=0:      Set product:2, TTL=3600
T=0:      Set product:3, TTL=3600
...
T=0:      Set product:1000, TTL=3600

T=3600:   ALL 1000 keys expire simultaneously!
          → 1000 DB queries at once 💥
─────────────────────────────────────────────────────────
```

### Why It Happens

- Cache populated during deployment
- Batch cache warming with same TTL
- Scheduled cache refresh

---

## 4. Cache Penetration

### The Problem

Requests for **non-existent data** always miss cache and hit database.

```
Request: GET /user/999999999  (doesn't exist)
─────────────────────────────────────────────────────────
1. Check cache → MISS (not cached)
2. Query DB    → NULL (doesn't exist)
3. Return 404
4. Next request → Repeat steps 1-3!
─────────────────────────────────────────────────────────
```

### Why It's Dangerous

- Attacker can flood with non-existent IDs
- Every request hits database
- No caching benefit

### Real-World Example

```
Attacker sends:
GET /user/-1
GET /user/-2
GET /user/-3
...
GET /user/-1000000

All hit DB directly → DoS attack via cache bypass
```

---

## 5. Cache Inconsistency

### The Problem

**Cache and database get out of sync**.

```
Timeline:
─────────────────────────────────────────────────────────
T=0:  Cache: price=$100, DB: price=$100  ✅ In sync
T=1:  Update DB: price=$150
T=2:  Cache invalidation fails (network issue)
T=3:  Cache: price=$100, DB: price=$150  ❌ Out of sync!
─────────────────────────────────────────────────────────
```

### Why It Happens

- Failed cache invalidation
- Race conditions in write operations
- Network partitions
- Multiple app instances with different timing

---

## Summary: Problems at a Glance

| Problem | Cause | Impact |
|---------|-------|--------|
| **Thundering Herd** | Cache expires, many concurrent requests | DB overload |
| **Hot Keys** | Uneven traffic distribution | Single point bottleneck |
| **Cache Avalanche** | Mass expiration at same time | DB overload |
| **Cache Penetration** | Requests for non-existent data | Cache bypass, DB load |
| **Cache Inconsistency** | Failed invalidation, race conditions | Stale/wrong data |

---

## Next: Solutions

In the next document, we'll cover solutions for each of these problems:
- Locking / Mutex
- Request coalescing
- Jittered TTLs
- Negative caching
- Cache warming

