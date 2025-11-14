# Redis Core Concepts

## What is Redis?

**Redis** = **RE**mote **DI**ctionary **S**erver

It's an in-memory data structure store that can be used as:
- Database
- Cache
- Message broker
- Streaming engine

## Redis Data Structures

### 1. Strings

The most basic Redis type - can store any data up to 512MB.

**Use cases**: Simple caching, counters, flags, serialized objects

```bash
# Set a value
SET user:1000:name "John Doe"

# Get a value
GET user:1000:name
# Returns: "John Doe"

# Set with expiration (EX = seconds)
SET session:abc123 "user_data" EX 3600

# Set if not exists (atomic)
SETNX lock:resource:1 "locked"

# Increment (atomic - perfect for counters)
SET page_views 0
INCR page_views
# Returns: 1
INCR page_views
# Returns: 2

# Increment by amount
INCRBY page_views 10
# Returns: 12

# Multiple operations
MSET user:1:name "Alice" user:2:name "Bob"
MGET user:1:name user:2:name
# Returns: ["Alice", "Bob"]
```

**Python Example:**
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Basic operations
r.set('greeting', 'Hello Redis!')
print(r.get('greeting'))  # Output: Hello Redis!

# With expiration
r.setex('temp_token', 300, 'abc123')  # Expires in 300 seconds

# Counter
r.set('api_calls', 0)
r.incr('api_calls')
print(r.get('api_calls'))  # Output: 1
```

---

### 2. Hashes

Perfect for representing objects (like a row in a database).

**Use cases**: User profiles, product data, configuration settings

```bash
# Set hash fields
HSET user:1000 name "John Doe" email "john@example.com" age 30

# Get a single field
HGET user:1000 name
# Returns: "John Doe"

# Get all fields
HGETALL user:1000
# Returns: ["name", "John Doe", "email", "john@example.com", "age", "30"]

# Get multiple fields
HMGET user:1000 name email
# Returns: ["John Doe", "john@example.com"]

# Increment a hash field
HINCRBY user:1000 login_count 1

# Check if field exists
HEXISTS user:1000 name
# Returns: 1 (true)

# Get all field names
HKEYS user:1000
# Returns: ["name", "email", "age"]
```

**Python Example:**
```python
# Store user as a hash
r.hset('user:1000', mapping={
    'name': 'John Doe',
    'email': 'john@example.com',
    'age': 30,
    'premium': True
})

# Get specific field
name = r.hget('user:1000', 'name')
print(name)  # Output: John Doe

# Get all fields
user = r.hgetall('user:1000')
print(user)  # Output: {'name': 'John Doe', 'email': 'john@example.com', ...}

# Update a field
r.hset('user:1000', 'age', 31)
```

**Strings vs Hashes:**
```python
# Strings (serialized object) - must serialize entire object
r.set('user:1000', json.dumps({'name': 'John', 'age': 30}))

# Hashes (structured) - can update individual fields
r.hset('user:1000', mapping={'name': 'John', 'age': 30})
r.hset('user:1000', 'age', 31)  # Update only age
```

---

### 3. Lists

Ordered collections of strings. Implemented as linked lists.

**Use cases**: Activity feeds, message queues, recent items

```bash
# Push to the left (beginning)
LPUSH notifications "New message from Alice"
LPUSH notifications "Bob liked your post"

# Push to the right (end)
RPUSH notifications "System update available"

# Get elements (0 = first, -1 = last)
LRANGE notifications 0 -1
# Returns: ["Bob liked your post", "New message from Alice", "System update available"]

# Get length
LLEN notifications
# Returns: 3

# Pop from left (removes and returns)
LPOP notifications
# Returns: "Bob liked your post"

# Pop from right
RPOP notifications

# Get specific element
LINDEX notifications 0

# Trim list to keep only N elements
LTRIM notifications 0 99  # Keep only first 100 items
```

**Python Example:**
```python
# Recent activity feed
r.lpush('user:1000:feed', 'Logged in')
r.lpush('user:1000:feed', 'Updated profile')
r.lpush('user:1000:feed', 'Posted a comment')

# Get latest 10 activities
recent = r.lrange('user:1000:feed', 0, 9)
print(recent)

# Keep only last 100 activities
r.ltrim('user:1000:feed', 0, 99)
```

---

### 4. Sets

Unordered collections of unique strings.

**Use cases**: Tags, unique visitors, relationships

```bash
# Add members
SADD tags:article:1 "python" "redis" "caching"

# Check membership
SISMEMBER tags:article:1 "python"
# Returns: 1 (true)

# Get all members
SMEMBERS tags:article:1
# Returns: ["python", "redis", "caching"]

# Count members
SCARD tags:article:1
# Returns: 3

# Set operations
SADD user:1:interests "python" "redis" "docker"
SADD user:2:interests "redis" "kubernetes" "docker"

# Intersection (common interests)
SINTER user:1:interests user:2:interests
# Returns: ["redis", "docker"]

# Union (all interests)
SUNION user:1:interests user:2:interests
# Returns: ["python", "redis", "docker", "kubernetes"]

# Difference
SDIFF user:1:interests user:2:interests
# Returns: ["python"]
```

**Python Example:**
```python
# Track unique visitors
r.sadd('visitors:2024-11-14', 'user:1', 'user:2', 'user:3')
r.sadd('visitors:2024-11-14', 'user:1')  # Duplicate - won't add

# Count unique visitors
count = r.scard('visitors:2024-11-14')
print(count)  # Output: 3
```

---

### 5. Sorted Sets (ZSETs)

Sets where each member has a score, sorted by score.

**Use cases**: Leaderboards, rate limiting, priority queues, trending items

```bash
# Add members with scores
ZADD leaderboard 100 "player1" 250 "player2" 180 "player3"

# Get members by rank (ascending)
ZRANGE leaderboard 0 -1 WITHSCORES
# Returns: ["player1", "100", "player3", "180", "player2", "250"]

# Get members by rank (descending)
ZREVRANGE leaderboard 0 -1 WITHSCORES
# Returns: ["player2", "250", "player3", "180", "player1", "100"]

# Get top 3
ZREVRANGE leaderboard 0 2

# Increment score
ZINCRBY leaderboard 50 "player1"

# Get rank
ZREVRANK leaderboard "player1"
# Returns: 1 (0-indexed, so this is 2nd place)

# Get score
ZSCORE leaderboard "player1"

# Count members in score range
ZCOUNT leaderboard 100 200
```

**Python Example:**
```python
# Leaderboard
r.zadd('game:leaderboard', {
    'player1': 1000,
    'player2': 1500,
    'player3': 1200
})

# Get top 10 players
top_players = r.zrevrange('game:leaderboard', 0, 9, withscores=True)
for player, score in top_players:
    print(f"{player}: {score}")
```

---

## Key Redis Concepts

### 1. Keys

Keys are binary-safe strings. Good naming conventions:

```bash
# Recommended patterns
user:1000:profile
session:abc123
cache:api:weather:london
rate_limit:user:1000:2024-11-14

# Use colons for namespacing
object:id:field

# Avoid very long keys (waste memory)
# Avoid very short keys (u1000 vs user:1000 - clarity matters)
```

### 2. Key Expiration (TTL)

```bash
# Set expiration when creating
SET key "value" EX 60  # Expires in 60 seconds

# Set expiration on existing key
EXPIRE key 60

# Check TTL
TTL key
# Returns: remaining seconds, -1 = no expiration, -2 = doesn't exist

# Remove expiration
PERSIST key
```

**Python Example:**
```python
# Set with expiration
r.setex('temp_data', 300, 'value')  # Expires in 300 seconds

# Set expiration on existing key
r.set('key', 'value')
r.expire('key', 600)

# Check TTL
ttl = r.ttl('key')
print(f"Expires in {ttl} seconds")
```

### 3. Atomic Operations

Redis commands are **atomic** - no race conditions!

```python
# Multiple clients incrementing - always correct
r.incr('counter')  # Thread-safe!

# Compare with non-atomic alternative:
count = r.get('counter')  # 1. Read
count = int(count) + 1     # 2. Increment
r.set('counter', count)    # 3. Write
# ❌ Race condition: another client might update between steps 1 and 3
```

---

## 🎯 Key Takeaways

1. **Strings**: Simple values, counters, serialized objects
2. **Hashes**: Structured objects (users, products)
3. **Lists**: Ordered sequences (feeds, queues)
4. **Sets**: Unique collections (tags, visitors)
5. **Sorted Sets**: Ranked data (leaderboards, trending)
6. **Keys**: Use clear naming conventions with colons
7. **TTL**: Always set expiration for cache data
8. **Atomic**: Redis operations are thread-safe

---

**Next**: [TTL and Eviction Policies](./03-ttl-and-eviction.md)

