# Thundering Herd Demo

Demonstrates the thundering herd problem and how to solve it with locking.

## Quick Start

```bash
chmod +x start.sh stop.sh
./start.sh
```

Open: http://localhost:8004

## The Problem

When cache expires and many requests come in simultaneously:

```
Without protection:
10 concurrent requests → 10 database queries 💥
```

## The Solution

Use locking so only one request queries the database:

```
With locking:
10 concurrent requests → 1 database query ✅
(9 requests wait for cache to be populated)
```

## Test It

In a new terminal:

```bash
docker exec -it thundering-herd-api python test_stampede.py
```

## Expected Output

```
============================================================
Testing: ❌ UNSAFE (No Protection)
============================================================
  Request  1: 💾 database (2015ms)
  Request  2: 💾 database (2018ms)
  Request  3: 💾 database (2020ms)
  ...
Database queries: 10

============================================================
Testing: ✅ SAFE (With Locking)
============================================================
  Request  1: 💾 database (2012ms)
  Request  2: ✅ cache    (2105ms)
  Request  3: ✅ cache    (2108ms)
  ...
Database queries: 1

📊 SUMMARY
UNSAFE: 10 DB queries
SAFE:   1 DB query
DB load reduction: 90%
```

## How It Works

**Unsafe endpoint:**
```python
# Every miss = DB query
if not cache.get(key):
    data = query_db()  # Everyone does this!
```

**Safe endpoint:**
```python
# Try to get lock
if redis.set(lock_key, "1", nx=True, ex=5):
    data = query_db()  # Only winner does this
    cache.set(key, data)
else:
    wait_for_cache()  # Others wait
```

## Stop

```bash
./stop.sh
```

