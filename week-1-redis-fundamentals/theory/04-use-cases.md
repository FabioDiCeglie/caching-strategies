# Use Cases for Backend Engineers

## 1. Database Query Caching ⭐

**Problem**: Database queries are slow and expensive at scale

**Solution**: Cache query results in Redis

```python
import redis
import json
import hashlib
from typing import Optional

r = redis.Redis(decode_responses=True)

def get_user_by_id(user_id: int) -> Optional[dict]:
    """Simple cache-aside pattern"""
    cache_key = f"user:{user_id}"
    
    # Try cache first
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss - query database
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    
    # Store in cache (1 hour TTL)
    r.setex(cache_key, 3600, json.dumps(user))
    
    return user

def get_products_by_category(category: str, page: int = 1) -> list:
    """Cache complex queries with query hash"""
    # Create cache key from query parameters
    query_hash = hashlib.md5(f"{category}:{page}".encode()).hexdigest()
    cache_key = f"products:category:{query_hash}"
    
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Complex database query
    products = db.query("""
        SELECT p.*, COUNT(r.id) as review_count
        FROM products p
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.category = ?
        GROUP BY p.id
        LIMIT 20 OFFSET ?
    """, category, (page - 1) * 20)
    
    # Cache for 10 minutes
    r.setex(cache_key, 600, json.dumps(products))
    
    return products
```

**Benefits**:
- 50-100x faster than database queries
- Reduces database load by 70-95%
- Lower cloud costs

---

## 2. Session Storage

**Problem**: Storing sessions in database is slow; in-memory sessions don't scale across servers

**Solution**: Store sessions in Redis for fast, distributed access

```python
import uuid
import json
from datetime import timedelta

class SessionManager:
    def __init__(self, redis_client):
        self.r = redis_client
        self.ttl = 1800  # 30 minutes
    
    def create_session(self, user_id: int, user_data: dict) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        key = f"session:{session_id}"
        
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            **user_data
        }
        
        # Store as hash for efficient field updates
        self.r.hset(key, mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in session_data.items()
        })
        self.r.expire(key, self.ttl)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session and refresh TTL"""
        key = f"session:{session_id}"
        
        if not self.r.exists(key):
            return None
        
        # Get session data
        session = self.r.hgetall(key)
        
        # Refresh expiration (sliding window)
        self.r.expire(key, self.ttl)
        
        return {k: json.loads(v) if v.startswith('{') or v.startswith('[') else v 
                for k, v in session.items()}
    
    def update_session(self, session_id: str, **fields):
        """Update specific session fields"""
        key = f"session:{session_id}"
        
        if self.r.exists(key):
            self.r.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in fields.items()
            })
            self.r.expire(key, self.ttl)
    
    def destroy_session(self, session_id: str):
        """Logout - delete session"""
        self.r.delete(f"session:{session_id}")

# Usage in FastAPI
from fastapi import FastAPI, Cookie, Response

app = FastAPI()
session_mgr = SessionManager(r)

@app.post("/login")
async def login(username: str, password: str, response: Response):
    # Verify credentials
    user = authenticate(username, password)
    
    # Create session
    session_id = session_mgr.create_session(user['id'], {
        'username': user['username'],
        'role': user['role']
    })
    
    # Set cookie
    response.set_cookie('session_id', session_id, httponly=True)
    return {"message": "Logged in successfully"}

@app.get("/profile")
async def get_profile(session_id: str = Cookie(None)):
    session = session_mgr.get_session(session_id)
    
    if not session:
        return {"error": "Not authenticated"}, 401
    
    return {"user": session}
```

**Benefits**:
- Fast session access (<1ms)
- Works across multiple servers
- Automatic cleanup with TTL
- Can handle millions of sessions

---

## 3. Rate Limiting

**Problem**: Protect API from abuse and implement usage quotas

**Solution**: Use Redis INCR with TTL for efficient rate limiting

```python
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_client):
        self.r = redis_client
    
    def check_rate_limit(
        self, 
        user_id: str, 
        max_requests: int = 100, 
        window_seconds: int = 60
    ) -> tuple[bool, dict]:
        """
        Sliding window rate limiter
        
        Returns: (allowed, info)
        """
        key = f"rate_limit:{user_id}:{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        
        pipe = self.r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        current_count, _ = pipe.execute()
        
        allowed = current_count <= max_requests
        remaining = max(0, max_requests - current_count)
        
        return allowed, {
            'limit': max_requests,
            'remaining': remaining,
            'reset_in': self.r.ttl(key)
        }

# Usage in FastAPI middleware
from fastapi import Request, HTTPException

rate_limiter = RateLimiter(r)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get user ID from auth or IP
    user_id = request.client.host
    
    allowed, info = rate_limiter.check_rate_limit(user_id)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                'X-RateLimit-Limit': str(info['limit']),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(info['reset_in'])
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers['X-RateLimit-Limit'] = str(info['limit'])
    response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
    
    return response
```

**Advanced: Token Bucket Algorithm**

```python
import time

class TokenBucketRateLimiter:
    def __init__(self, redis_client):
        self.r = redis_client
    
    def check_rate_limit(
        self,
        user_id: str,
        max_tokens: int = 100,
        refill_rate: float = 10  # tokens per second
    ) -> bool:
        """Token bucket algorithm for smooth rate limiting"""
        key = f"token_bucket:{user_id}"
        now = time.time()
        
        # Lua script for atomic operation
        lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add
        local time_passed = now - last_refill
        local tokens_to_add = time_passed * refill_rate
        tokens = math.min(max_tokens, tokens + tokens_to_add)
        
        -- Try to consume 1 token
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return 1
        else
            return 0
        end
        """
        
        result = self.r.eval(lua_script, 1, key, max_tokens, refill_rate, now)
        return bool(result)
```

---

## 4. Caching External API Responses

**Problem**: External APIs are slow and have rate limits

**Solution**: Cache responses with appropriate TTL

```python
import httpx
import json

async def get_weather(city: str) -> dict:
    """Cache external API responses"""
    cache_key = f"weather:{city.lower()}"
    
    # Try cache
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from external API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}"
        )
        data = response.json()
    
    # Cache for 10 minutes (weather doesn't change that fast)
    r.setex(cache_key, 600, json.dumps(data))
    
    return data

# With fallback for errors
async def get_weather_with_fallback(city: str) -> dict:
    cache_key = f"weather:{city.lower()}"
    
    try:
        # Try cache
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fetch from API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={city}",
                timeout=5.0
            )
            data = response.json()
        
        # Cache for 10 minutes
        r.setex(cache_key, 600, json.dumps(data))
        
        # Also store as backup (longer TTL, for fallback)
        r.setex(f"{cache_key}:backup", 86400, json.dumps(data))
        
        return data
        
    except Exception as e:
        # API failed - try backup cache
        backup = r.get(f"{cache_key}:backup")
        if backup:
            return json.loads(backup)
        raise e
```

---

## 5. Leaderboards and Rankings

**Problem**: Computing rankings from database is expensive

**Solution**: Use Redis Sorted Sets

```python
class Leaderboard:
    def __init__(self, redis_client, name: str):
        self.r = redis_client
        self.key = f"leaderboard:{name}"
    
    def add_score(self, player_id: str, score: int):
        """Add or update player score"""
        self.r.zadd(self.key, {player_id: score})
    
    def increment_score(self, player_id: str, points: int):
        """Increment player score"""
        self.r.zincrby(self.key, points, player_id)
    
    def get_top(self, n: int = 10) -> list:
        """Get top N players"""
        players = self.r.zrevrange(self.key, 0, n - 1, withscores=True)
        return [
            {"rank": i + 1, "player": p, "score": int(s)}
            for i, (p, s) in enumerate(players)
        ]
    
    def get_rank(self, player_id: str) -> Optional[dict]:
        """Get player rank and score"""
        rank = self.r.zrevrank(self.key, player_id)
        score = self.r.zscore(self.key, player_id)
        
        if rank is None:
            return None
        
        return {
            "player": player_id,
            "rank": rank + 1,  # Convert 0-based to 1-based
            "score": int(score)
        }
    
    def get_around_player(self, player_id: str, count: int = 5) -> list:
        """Get players around a specific player"""
        rank = self.r.zrevrank(self.key, player_id)
        
        if rank is None:
            return []
        
        start = max(0, rank - count)
        end = rank + count
        
        players = self.r.zrevrange(self.key, start, end, withscores=True)
        
        return [
            {
                "rank": start + i + 1,
                "player": p,
                "score": int(s),
                "is_current": p == player_id
            }
            for i, (p, s) in enumerate(players)
        ]

# Usage
leaderboard = Leaderboard(r, "global")

# Update scores
leaderboard.add_score("player123", 1000)
leaderboard.increment_score("player123", 50)

# Get rankings
top_players = leaderboard.get_top(10)
my_rank = leaderboard.get_rank("player123")
nearby = leaderboard.get_around_player("player123", count=3)
```

---

## 6. Distributed Locks

**Problem**: Coordinate work across multiple servers

**Solution**: Use Redis SETNX for distributed locking

```python
import time
import uuid

class DistributedLock:
    def __init__(self, redis_client, lock_name: str, timeout: int = 10):
        self.r = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())
    
    def acquire(self, blocking: bool = True, timeout: int = None) -> bool:
        """Acquire lock"""
        end_time = time.time() + (timeout or self.timeout)
        
        while True:
            # Try to set lock with our unique token
            if self.r.set(self.lock_name, self.token, nx=True, ex=self.timeout):
                return True
            
            if not blocking:
                return False
            
            if time.time() > end_time:
                return False
            
            time.sleep(0.1)
    
    def release(self):
        """Release lock (only if we own it)"""
        # Lua script to atomically check and delete
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        self.r.eval(lua_script, 1, self.lock_name, self.token)
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# Usage
async def process_payment(order_id: str):
    """Ensure only one server processes each payment"""
    lock = DistributedLock(r, f"payment:{order_id}")
    
    if lock.acquire(blocking=False):
        try:
            # Process payment
            result = await charge_credit_card(order_id)
            await update_order_status(order_id, "paid")
            return result
        finally:
            lock.release()
    else:
        raise Exception("Payment already being processed")

# Or with context manager
def send_email_once(user_id: str):
    """Ensure email is sent only once even with multiple workers"""
    with DistributedLock(r, f"email:welcome:{user_id}", timeout=5):
        send_welcome_email(user_id)
```

---

## 7. Real-time Analytics

**Problem**: Track metrics in real-time without database overhead

**Solution**: Use Redis data structures for fast counters and aggregations

```python
from datetime import datetime

class Analytics:
    def __init__(self, redis_client):
        self.r = redis_client
    
    def track_page_view(self, page: str, user_id: str = None):
        """Track page views"""
        today = datetime.now().strftime('%Y-%m-%d')
        hour = datetime.now().strftime('%Y-%m-%d-%H')
        
        pipe = self.r.pipeline()
        
        # Daily counter
        pipe.incr(f"pageviews:{page}:{today}")
        pipe.expire(f"pageviews:{page}:{today}", 86400 * 7)  # Keep 7 days
        
        # Hourly counter
        pipe.incr(f"pageviews:{page}:{hour}")
        pipe.expire(f"pageviews:{page}:{hour}", 3600 * 48)  # Keep 48 hours
        
        # Unique visitors (using HyperLogLog for memory efficiency)
        if user_id:
            pipe.pfadd(f"unique_visitors:{page}:{today}", user_id)
        
        pipe.execute()
    
    def get_page_stats(self, page: str) -> dict:
        """Get page statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        views = self.r.get(f"pageviews:{page}:{today}") or 0
        unique = self.r.pfcount(f"unique_visitors:{page}:{today}")
        
        return {
            "page": page,
            "views": int(views),
            "unique_visitors": unique
        }
    
    def get_trending_pages(self, top_n: int = 10) -> list:
        """Get trending pages in last hour"""
        hour = datetime.now().strftime('%Y-%m-%d-%H')
        
        # Get all pageview keys for current hour
        keys = self.r.keys(f"pageviews:*:{hour}")
        
        pages = []
        for key in keys:
            page = key.decode().split(':')[1]
            count = int(self.r.get(key) or 0)
            pages.append({"page": page, "views": count})
        
        return sorted(pages, key=lambda x: x['views'], reverse=True)[:top_n]
```

---

## 🎯 Key Takeaways

1. **Database Query Caching**: Reduce load and improve response times
2. **Session Storage**: Fast, distributed session management
3. **Rate Limiting**: Protect APIs from abuse efficiently
4. **API Response Caching**: Speed up external API calls
5. **Leaderboards**: Real-time rankings with Sorted Sets
6. **Distributed Locks**: Coordinate work across servers
7. **Real-time Analytics**: Track metrics without database overhead

---

**Next**: Start hands-on projects!

