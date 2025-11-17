# Mini-Project 3: Session Storage with Redis

Store user sessions using **Redis Hashes** for structured data.

**Session TTL**: 30 minutes (auto-renewed on each request)

## 🚀 Quick Start

```bash
# 1. Start Redis
cd ../../setup && docker-compose up -d

# 2. Install and run
cd ../mini-projects/session-storage
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Open **http://localhost:8002/docs** for API documentation.

## 🧪 Try It Out

```bash
# 1. Login (any username/password works)
curl -X POST http://localhost:8002/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "test123"}' \
  -c cookies.txt

# Response:
{
  "message": "Login successful",
  "username": "alice",
  "session_id": "abc-123-def-456"
}

# 2. Access protected route (sends cookie automatically)
curl http://localhost:8002/profile -b cookies.txt

# Response:
{
  "user_id": "user_1234",
  "username": "alice"
}

# 3. Logout (destroys session)
curl -X POST http://localhost:8002/logout -b cookies.txt

# 4. Try accessing profile again (fails)
curl http://localhost:8002/profile -b cookies.txt

# Response:
{
  "detail": "Session expired or invalid"
}
```

## 🔍 How It Works

**Redis Hashes store structured data:**
```python
# Create session
redis_client.hset("session:abc123", mapping={
    "user_id": "user_1234",
    "username": "alice",
    "created_at": "1700000000"
})
redis_client.expire("session:abc123", 1800)  # 30 minutes

# Get session
session = redis_client.hgetall("session:abc123")
```

**Cookie flow:**
```
Login → Server creates session → Sets cookie → Browser stores it
Request → Browser sends cookie → Server validates → Returns data
Logout → Server deletes session → Clears cookie
```

## 🔍 Explore Redis

```bash
docker exec -it redis-cache redis-cli

# View all sessions
KEYS session:*

# View session data
HGETALL session:abc-123-def-456

# Check TTL
TTL session:abc-123-def-456

# Delete session (logout)
DEL session:abc-123-def-456
```

## ✅ What You Learned

- Redis Hashes for structured data
- Session management with cookies
- Auto-expiring sessions with TTL
- Sliding window (TTL refreshes on each request)
- HttpOnly cookies for security
- Trade-off: Redis dependency vs instant logout capability

---

**🎉 Week 1 Complete!** You've mastered Redis fundamentals and built 3 production-ready patterns.

