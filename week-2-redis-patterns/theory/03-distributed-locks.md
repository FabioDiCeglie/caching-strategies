# Distributed Locks with Redis

## The Problem

```python
# Server 1 and Server 2 both try to process the same payment
# WITHOUT locks:

Server 1: Check if payment processed → No
Server 2: Check if payment processed → No
Server 1: Process payment → $100 charged
Server 2: Process payment → $100 charged AGAIN! ❌
```

**Solution:** Distributed lock ensures only ONE server processes at a time.

---

## Basic Lock Implementation

```python
import uuid
import time

class RedisLock:
    def __init__(self, redis_client, lock_name, timeout=10):
        self.redis = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())  # Unique ID for this lock
    
    def acquire(self):
        """Try to acquire the lock"""
        # SET lock_key token NX EX timeout
        # NX = only set if doesn't exist
        # EX = set expiration
        return self.redis.set(
            self.lock_name,
            self.token,
            nx=True,
            ex=self.timeout
        )
    
    def release(self):
        """Release the lock (only if we own it)"""
        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        return self.redis.eval(lua_script, 1, self.lock_name, self.token)
```

---

## Usage Example

```python
lock = RedisLock(redis_client, "payment:order_123")

if lock.acquire():
    try:
        # Critical section - only one server executes this
        process_payment(order_id)
        update_order_status(order_id)
    finally:
        lock.release()  # Always release!
else:
    print("Another server is processing this payment")
```

---

## Why UUID Token?

**Problem without token:**
```python
# Server 1 acquires lock
lock.set("payment:123", "1", ex=5)

# Server 1 takes 6 seconds (lock expires!)
time.sleep(6)

# Server 2 acquires lock (thinks it's free)
lock.set("payment:123", "1", ex=5)

# Server 1 finishes and deletes lock
lock.delete("payment:123")  # ❌ Deletes Server 2's lock!

# Server 3 can now acquire lock while Server 2 is still working! 💥
```

**Solution with token:**
```python
# Server 1 acquires with unique token
lock.set("payment:123", "abc-123", ex=5)

# Server 1's lock expires, Server 2 gets it
lock.set("payment:123", "def-456", ex=5)

# Server 1 tries to delete
if lock.get("payment:123") == "abc-123":  # False!
    lock.delete("payment:123")  # Won't delete
# ✅ Server 2's lock is safe
```

---

## Context Manager (Pythonic Way)

```python
class RedisLock:
    # ... (previous code)
    
    def __enter__(self):
        if not self.acquire():
            raise Exception("Could not acquire lock")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Usage
with RedisLock(redis_client, "payment:order_123"):
    process_payment(order_id)
    # Lock auto-released even if exception occurs
```

---

## Blocking Lock (Wait Until Available)

```python
def acquire_blocking(self, blocking_timeout=30):
    """Wait for lock to become available"""
    start = time.time()
    
    while time.time() - start < blocking_timeout:
        if self.acquire():
            return True
        time.sleep(0.1)  # Wait 100ms before retry
    
    return False  # Timeout

# Usage
lock = RedisLock(redis_client, "payment:order_123")
if lock.acquire_blocking(timeout=30):
    try:
        process_payment(order_id)
    finally:
        lock.release()
```

---

## Common Use Cases

### 1. Prevent Duplicate Processing

```python
def send_welcome_email(user_id):
    lock = RedisLock(redis_client, f"email:welcome:{user_id}")
    
    if lock.acquire():
        try:
            send_email(user_id)
        finally:
            lock.release()
    else:
        print(f"Email already being sent by another worker")
```

### 2. Cron Job Coordination

```python
# Only one server runs the daily cleanup
def daily_cleanup():
    lock = RedisLock(redis_client, "cron:daily_cleanup", timeout=3600)
    
    if not lock.acquire():
        return  # Another server is running it
    
    try:
        cleanup_old_data()
        send_reports()
    finally:
        lock.release()
```

### 3. Rate Limit Critical Operations

```python
def expensive_operation():
    lock = RedisLock(redis_client, "expensive_op", timeout=60)
    
    # Only allow one instance to run
    if not lock.acquire():
        return {"error": "Operation already in progress"}
    
    try:
        result = perform_expensive_computation()
        return result
    finally:
        lock.release()
```

---

## Advanced: Redlock Algorithm

For **multi-Redis setups** (Redis cluster), use Redlock:

```python
from redlock import Redlock

# Connect to multiple Redis instances
redlock = Redlock([
    {"host": "redis1", "port": 6379},
    {"host": "redis2", "port": 6379},
    {"host": "redis3", "port": 6379},
])

# Acquire lock on majority of instances
lock = redlock.lock("payment:123", 10000)  # 10 second timeout

if lock:
    try:
        process_payment()
    finally:
        redlock.unlock(lock)
```

**When to use Redlock:**
- Multiple Redis instances
- High availability required
- Critical operations (payments, inventory)

---

## Pitfalls & Solutions

### Pitfall 1: Lock Held Too Long

**Problem:**
```python
lock = RedisLock(redis_client, "job", timeout=5)
lock.acquire()
long_running_task()  # Takes 10 seconds
lock.release()  # ❌ Lock already expired at 5 seconds!
```

**Solutions:**
1. Set longer timeout
2. Implement lock renewal (heartbeat)
3. Break task into smaller chunks

### Pitfall 2: Deadlocks

**Problem:**
```python
# Function A acquires lock1, needs lock2
# Function B acquires lock2, needs lock1
# Both wait forever! 💀
```

**Solution:**
- Always acquire locks in same order
- Use timeout on acquire
- Implement deadlock detection

### Pitfall 3: Forgetting to Release

**Problem:**
```python
lock.acquire()
if error_condition:
    return  # ❌ Lock never released!
process_payment()
lock.release()
```

**Solution:**
- Always use try/finally
- Or use context manager (with statement)

---

## Best Practices

1. **Always set expiration** - Prevent stuck locks
2. **Use unique tokens** - Prevent deleting others' locks
3. **Use context managers** - Automatic cleanup
4. **Set appropriate timeout** - Not too short, not too long
5. **Handle acquire failure** - Don't assume you got the lock
6. **Monitor lock duration** - Track how long operations take

---

## Monitoring

```python
import time

class MonitoredLock(RedisLock):
    def acquire(self):
        self.start_time = time.time()
        return super().acquire()
    
    def release(self):
        duration = time.time() - self.start_time
        # Log to metrics system
        metrics.histogram('lock.duration', duration, tags=['lock:' + self.lock_name])
        return super().release()
```

---

## Key Takeaways

1. **Use locks for critical operations** - Payments, emails, cron jobs
2. **Always use unique tokens** - Prevent accidental deletion
3. **Set appropriate timeouts** - Balance safety vs stuck locks
4. **Use context managers** - Ensure cleanup
5. **Monitor lock metrics** - Duration, failures, contention

---

## When NOT to Use Locks

❌ **High-frequency operations** - Locks add latency
❌ **Read-only operations** - No conflict risk
❌ **Independent tasks** - No shared resources
❌ **Local single-server** - Use threading locks instead

✅ **DO use for:**
- Payments, financial transactions
- One-time operations (email sending)
- Cron jobs across servers
- Resource coordination

---

**Next**: Start building the hands-on project!

