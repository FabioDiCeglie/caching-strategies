# Cache Penetration Demo

Demonstrates cache penetration attacks and how negative caching prevents them.

## Quick Start

```bash
chmod +x start.sh stop.sh
./start.sh
```

Open: http://localhost:8007

## The Problem

Requests for **non-existent data** always miss cache → hit database.

```
Attacker sends:
GET /user/999999    → Cache miss → DB query → Not found
GET /user/999999    → Cache miss → DB query → Not found  (again!)
GET /user/999999    → Cache miss → DB query → Not found  (again!)
...
Cache provides ZERO protection!
```

## The Solution

**Negative caching**: Cache "not found" results too.

```
GET /user/999999    → Cache miss → DB query → Not found → Cache "NULL"
GET /user/999999    → Cache HIT (NULL) → Return "not found" immediately
GET /user/999999    → Cache HIT (NULL) → No DB query!
```

## Test It

```bash
docker exec -it cache-penetration-api python test_penetration.py
```

## Expected Output

```
UNSAFE: 100 DB queries (every request hits DB) 💥
SAFE:   10 DB queries (negative cache blocks repeats) ✅

⚡ Negative caching reduced DB load by 90%!
```

## How It Works

```python
# Without negative caching
if not cached:
    user = db.get(user_id)
    if user:
        cache.set(key, user)  # Only cache found items
    return user

# With negative caching
if cached == "NULL":
    return None  # Known to not exist

if not cached:
    user = db.get(user_id)
    if user:
        cache.set(key, user, ttl=300)
    else:
        cache.set(key, "NULL", ttl=60)  # Cache not-found too!
    return user
```

## Stop

```bash
./stop.sh
```

