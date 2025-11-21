# Cache Invalidation Strategies

Complete demonstration of **7 cache invalidation patterns** used in production systems.

## 🎯 What You'll Learn

- When and how to invalidate cached data
- Trade-offs between different strategies
- Event-based invalidation with Redis Pub/Sub
- Production-ready combined approach

## 🚀 Quick Start

**Prerequisites:** Docker

```bash
# Start everything (Postgres + Redis + FastAPI)
chmod +x start.sh stop.sh
./start.sh

# Run all strategy tests
docker exec -it shop-api python test_strategies.py

# Stop and clean
./stop.sh
```

## 📚 The 7 Strategies

### 1. TTL (Time To Live) ⏰

**Concept:** Cache expires automatically after X seconds

**Endpoint:** `GET /products/ttl/{id}`

**How it works:**
```python
cache.set("product:1", data, ttl=60)  # Expires in 60s
# After 60s: automatic deletion
# Next request: cache miss → fresh from DB
```

**Pros:** Simple, automatic cleanup  
**Cons:** Data can be stale until TTL expires  
**Best for:** Data that changes infrequently

---

### 2. Explicit Invalidation 🗑️

**Concept:** Manually delete cache when data changes

**Endpoints:**
- `GET /products/explicit/{id}` - Get product
- `DELETE /products/explicit/{id}` - Delete product (invalidates cache)

**How it works:**
```python
# Update database
db.update(product)

# Delete cache immediately
cache.delete("product:1")

# Next read: cache miss → fresh data
```

**Pros:** Immediate consistency  
**Cons:** Next read is slow (cache miss)  
**Best for:** Critical data that must be fresh

---

### 3. Write-Through ✏️

**Concept:** Update cache AND database on writes

**Endpoints:**
- `GET /products/writethrough/{id}` - Get product
- `PUT /products/writethrough/{id}` - Update product (updates cache too!)

**How it works:**
```python
# Update database
db.update(product)

# Update cache with NEW data (not delete!)
cache.set("product:1", new_data, ttl=300)

# Next read: cache hit (FAST!)
```

**Pros:** Next read is fast, cache always fresh  
**Cons:** Writes are slower (2 operations)  
**Best for:** Frequently-read data after updates

---

### 4. Event-Based (Pub/Sub) 📢

**Concept:** Publish events when data changes, subscribers invalidate

**Endpoints:**
- `GET /products/events/{id}` - Get product
- `PUT /products/events/{id}` - Update product (publishes event)

**How it works:**
```python
# Service A: Update & publish
db.update(product)
redis.publish("product:updates", {"product_id": 1})
cache.delete("product:1")  # Invalidate own cache

# Service B: Listening (worker.py)
# Receives event → invalidates ITS OWN cache
```

**Pros:** Decoupled services, scales across microservices  
**Cons:** Complex, eventual consistency  
**Best for:** Microservices architecture

**🎧 Try the Worker:**
```bash
# Terminal 1 - Start worker (Service B)
docker exec -it shop-api python worker.py

# Terminal 2 - Run tests (Service A)
docker exec -it shop-api python test_strategies.py
```

**Why the worker?**

In production, you'd have multiple services:
- **Service A (API):** Updates product → publishes event
- **Service B (Cart):** Listens → invalidates cart cache
- **Service C (Search):** Listens → invalidates search cache
- **Service D (Recommendations):** Listens → invalidates reco cache

The worker simulates Service B - a separate microservice with its own cache that responds to events!

---

### 5. SWR (Stale-While-Revalidate) ⚡

**Concept:** Return cached data immediately (even if stale), refresh in background

**Endpoint:** `GET /products/featured`

**How it works:**
```python
cached = cache.get("featured")
ttl = cache.ttl("featured")

if cached and ttl < 30:  # Stale but exists
    # Return immediately (FAST!)
    background_refresh()  # Refresh for next request
    return cached

# Otherwise return cached or fresh
```

**Pros:** Always fast, no cache stampede  
**Cons:** Users might see slightly stale data  
**Best for:** High-traffic endpoints (used by Vercel, Next.js, CDNs)

---

### 6. Cache Tags 🏷️

**Concept:** Tag related cache entries, invalidate by tag

**Endpoints:**
- `GET /products/by-category/{id}` - Get all products in category
- `PUT /categories/{id}` - Update category (invalidates ALL products with tag!)

**How it works:**
```python
# Cache with tags
cache.set("products:category:1", data, tags=["category:1"])
cache.set("product:5", data, tags=["category:1"])

# Later: invalidate ALL with tag
cache.invalidate_by_tag("category:1")
# → Both entries deleted!
```

**Pros:** Invalidate many related items at once  
**Cons:** Extra storage for tags  
**Best for:** Complex data relationships

---

### 7. PRODUCTION (Combined) 🔥

**Concept:** Use multiple strategies together

**Endpoints:**
- `GET /products/production/{id}` - Get product
- `PUT /products/production/{id}` - Update product (uses ALL strategies!)

**How it works:**
```python
# On write:
db.update(product)

# 1. Explicit delete (immediate consistency)
cache.delete("product:1")

# 2. Publish event (for other services)
redis.publish("product:updates", {"product_id": 1})

# 3. Invalidate by tag (related data)
cache.invalidate_by_tag(f"category:{product.category_id}")

# 4. TTL as safety net (always set TTL!)
# Already included in cache.set(..., ttl=300)
```

**This is how REAL systems do it!** ⭐

Combines:
- ✅ TTL (safety net)
- ✅ Explicit delete (immediate)
- ✅ Events (microservices)
- ✅ Tags (relationships)

---

## 🧪 Testing

**Run all strategies:**
```bash
docker exec -it shop-api python test_strategies.py
```

**Test specific strategy:**
```bash
# Via API docs
open http://localhost:8004/docs

# Or curl
curl http://localhost:8004/products/ttl/1
curl http://localhost:8004/products/writethrough/1
curl http://localhost:8004/products/production/1
```

**Check cache stats:**
```bash
curl http://localhost:8004/cache/stats/product:ttl:1
```

---

## 📊 Performance Comparison

| Strategy | Read Speed | Write Speed | Consistency | Complexity |
|----------|------------|-------------|-------------|------------|
| TTL | Fast (cache hit) | Fast | Eventual | Low ⭐ |
| Explicit | Slow after write | Fast | Strong | Low ⭐ |
| Write-Through | Fast always | Slow | Strong | Medium |
| Event-Based | Fast | Fast | Eventual | High |
| SWR | Very Fast | Fast | Eventual | High |
| Cache Tags | Fast | Medium | Strong | High |
| **Production** | **Fast** | **Medium** | **Strong** | **Medium** ⭐ |

---

## 🐳 Docker Services

- **postgres-shop-api** - PostgreSQL (port 5433)
- **redis-shop-api** - Redis (port 6380)
- **shop-api** - FastAPI (port 8004)

**View logs:**
```bash
docker compose logs -f app
```

**Access Redis CLI:**
```bash
docker exec -it redis-shop-api redis-cli
> KEYS product:*
> GET product:ttl:1
> TTL product:ttl:1
```

**Access Postgres:**
```bash
docker exec -it postgres-shop-api psql -U shop_user -d shop_db
# SELECT * FROM products;
# SELECT * FROM categories;
```

---

## 📁 Project Structure

```
.
├── main.py              # FastAPI with 7 strategy endpoints
├── cache.py             # Cache manager with all strategies
├── database.py          # Products & Categories models
├── worker.py            # Event subscriber (Service B simulation)
├── test_strategies.py   # Comprehensive test suite
├── docker-compose.yml   # All services
├── Dockerfile
└── README.md
```

---

## 🔑 Key Takeaways

1. **Always use TTL** - Even with other strategies (safety net)
2. **Explicit invalidation** - Simplest for critical data
3. **Write-Through** - Best for read-heavy after writes
4. **Event-Based** - Essential for microservices
5. **SWR** - Best for high traffic (users don't wait)
6. **Cache Tags** - Powerful for relationships
7. **Production = Combine strategies** - Don't pick just one!

---
