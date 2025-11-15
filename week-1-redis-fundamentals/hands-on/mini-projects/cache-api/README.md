# Mini-Project 1: Cache a Slow API

Learn the **cache-aside pattern** by wrapping a slow external API with Redis caching.

**Performance**: ~200-500ms without cache → ~1-5ms with cache (40-500x faster!)

## 🚀 Quick Start

```bash
# 1. Start Redis (from setup directory)
cd ../../setup && docker-compose up -d

# 2. Install and run
cd ../mini-projects/cache-api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Open **http://localhost:8000/docs** for interactive API documentation.

## 🧪 Try It Out

```bash
# First call - slow (cache miss)
curl http://localhost:8000/users/1
# Response: "cached": false, "response_time_ms": ~200-500

# Second call - fast! (cache hit)
curl http://localhost:8000/users/1
# Response: "cached": true, "response_time_ms": ~1-5

# Compare with non-cached endpoint
curl http://localhost:8000/users/1/nocache
# Always slow: ~200-500ms

# Check TTL in Redis
docker exec -it redis-cache redis-cli TTL user:1

# Clear cache
curl -X POST http://localhost:8000/cache/clear
```

## 🔍 Explore Redis

```bash
# Connect to Redis CLI
docker exec -it redis-cache redis-cli

# View cached keys
KEYS *

# Check a value
GET user:1

# Check TTL
TTL user:1
```

Or open **http://localhost:8081** for Redis Commander (GUI).

## 📈 Experiments

**Test TTL expiration:**
```bash
curl "http://localhost:8000/posts/1?ttl=30"  # 30 second TTL
docker exec -it redis-cache redis-cli TTL post:1
```

**Fill the cache:**
```bash
for i in {1..10}; do curl http://localhost:8000/users/$i; done
docker exec -it redis-cache redis-cli DBSIZE
```

## ✅ What You Learned

- Cache-aside pattern implementation
- TTL-based expiration
- 40-500x performance improvement
- Trade-off: speed vs data freshness

---

**Next**: [Mini-Project 2: Rate Limiter](../rate-limiter/)

