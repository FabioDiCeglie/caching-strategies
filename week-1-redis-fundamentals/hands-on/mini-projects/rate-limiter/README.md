# Mini-Project 2: Rate Limiter with Redis

Protect APIs using **Redis INCR** for atomic rate limiting.

**Limit**: 5 requests per minute (fixed window)

## 🚀 Quick Start

```bash
# 1. Start Redis
cd ../../setup && docker-compose up -d

# 2. Install and run
cd ../mini-projects/rate-limiter
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Open **http://localhost:8001/docs** for API documentation.

## 🧪 Try It Out

```bash
# Make 5 requests (all succeed)
curl http://localhost:8001/api/status  # ✅ Request 1
curl http://localhost:8001/api/status  # ✅ Request 2
curl http://localhost:8001/api/status  # ✅ Request 3
curl http://localhost:8001/api/status  # ✅ Request 4
curl http://localhost:8001/api/status  # ✅ Request 5

# 6th request blocked
curl -i http://localhost:8001/api/status

# Response:
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 45 seconds

{
  "detail": "Rate limit exceeded"
}

# Wait for next minute, then resets automatically ✅
```

## 🔍 How It Works

**Core logic:**
```python
current = redis_client.incr(key)  # Atomic increment
if current == 1:
    redis_client.expire(key, 60)  # Set TTL
allowed = current <= 5            # Check limit
```

**Key format:**
```
rate_limit:127.0.0.1:2024-11-16-14-30  # Resets every minute
```

**Apply to endpoints:**
```python
@app.get("/api/status")
async def get_status(rate_limit: dict = Depends(rate_limit_dependency)):
    # Rate limited endpoint
```

## 🔍 Explore Redis

```bash
docker exec -it redis-cache redis-cli

# View keys
KEYS rate_limit:*

# Check counter
GET rate_limit:127.0.0.1:2024-11-16-14-30

# Check TTL
TTL rate_limit:127.0.0.1:2024-11-16-14-30
```

## ✅ What You Learned

- Redis INCR for atomic counters
- Fixed window rate limiting
- FastAPI dependency injection
- HTTP 429 responses
- Trade-off: Simple but allows bursts at window boundary

---

**Next**: [Mini-Project 3: Session Storage](../session-storage/)

