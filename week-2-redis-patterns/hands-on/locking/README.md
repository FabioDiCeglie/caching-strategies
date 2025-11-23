## Distributed Locks with Redis

Demonstrates how Redis prevents **race conditions** in concurrent systems.

## 🎯 The Problem

**Scenario:** An event has 1 ticket left. 5 users try to book simultaneously.

**Without Lock (Race Condition):**
```
User A: Read DB → 1 ticket available ✅
User B: Read DB → 1 ticket available ✅  ← BOTH see 1!
User A: Book ticket → Set available = 0
User B: Book ticket → Set available = -1  ← OVERSOLD!
```

**With Lock (Safe):**
```
User A: Acquire lock ✅ → Read 1 → Book → Release lock
User B: Try lock → WAIT ⏳
User B: Acquire lock ✅ → Read 0 → Fail ❌
```

## 🚀 Quick Start

```bash
# Start everything
chmod +x start.sh stop.sh
./start.sh

# Run concurrent booking test
docker exec -it booking-api python test_concurrent.py

# Stop and clean
./stop.sh
```

## 📚 API Endpoints

**Without Lock (Dangerous):**
- `POST /book-no-lock/{event_id}` - Race condition possible

**With Lock (Safe):**
- `POST /book-with-lock/{event_id}` - Serialized access

**Utility:**
- `GET /events/{event_id}` - Check event status
- `POST /reset/{event_id}` - Reset for testing

## 🧪 Testing

The test simulates 10 concurrent booking requests for 1 ticket.

**Expected Results:**
- **WITHOUT LOCK:** May oversell (timing-dependent)
- **WITH LOCK:** Exactly 1 booking (guaranteed)

**Note:** Race conditions are **timing-dependent** and may not always reproduce in tests. The key learning is that locks **guarantee** they can't happen, regardless of timing.

## 🔑 How Redis Locks Work

### The Implementation

```python
# Acquire lock
redis.set(
    "lock:event:1",
    unique_id,
    nx=True,    # Only if key doesn't exist
    ex=10       # Expire after 10 seconds (safety)
)

# Critical section - only one request at a time
# ... process booking ...

# Release lock (atomic check + delete)
if redis.get("lock:event:1") == unique_id:
    redis.delete("lock:event:1")
```

### Key Features

1. **Atomic Operations** - `SET NX EX` is atomic in Redis
2. **Unique Lock ID** - Ensures only lock owner can release
3. **TTL Safety Net** - Lock expires if process crashes
4. **Lua Script** - Atomic check-and-delete on release

## 💡 Why This Matters

### Real-World Use Cases

1. **Ticket Booking** - Prevent overselling
2. **Inventory Management** - Prevent negative stock
3. **Payment Processing** - Prevent double charges
4. **Resource Allocation** - Prevent double booking

### The Race Window

```
WITHOUT LOCK:
Time 0ms:  User A reads available_tickets = 1
Time 5ms:  User B reads available_tickets = 1  ← RACE!
Time 10ms: User A writes available_tickets = 0
Time 15ms: User B writes available_tickets = 0  ← Should be -1!
Result: Both think they booked the last ticket

WITH LOCK:
Time 0ms:  User A acquires lock, reads 1
Time 5ms:  User B tries lock → BLOCKED ⏳
Time 10ms: User A writes 0, releases lock
Time 15ms: User B acquires lock, reads 0 → FAILS
Result: Only User A books the ticket ✅
```

## 🐳 Architecture

```
┌─────────────────┐
│  FastAPI App    │
│                 │
│  ┌───────────┐  │
│  │ Endpoint  │  │ ← Multiple concurrent requests
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │Redis Lock │  │ ← Serializes access
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Database  │  │ ← Protected from races
│  └───────────┘  │
└─────────────────┘
```

## 📁 Files

- `main.py` - FastAPI with locking endpoints
- `locks.py` - Redis lock implementation
- `redis_client.py` - Redis connection manager
- `database.py` - Events & Bookings models
- `test_concurrent.py` - Concurrent booking simulation

## 🔒 Best Practices

1. **Always set TTL** - Locks should expire (10-30 seconds)
2. **Use unique lock IDs** - UUID per request
3. **Atomic operations** - Use Redis SET NX EX
4. **Lua scripts** - Atomic check-and-delete
5. **Handle failures** - Release locks in `finally` blocks
6. **Short critical sections** - Hold locks briefly

## ⚠️ Common Pitfalls

1. **Forgetting to release** - Always use try/finally
2. **No TTL** - Lock held forever if process crashes
3. **Not checking ownership** - Anyone can delete lock
4. **Long critical sections** - Other requests timeout
5. **Wrong isolation level** - Database still has races

