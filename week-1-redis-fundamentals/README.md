# Week 1 — Redis Fundamentals + Use Cases

⭐ **Goal**: Understand why caching matters & become fluent with Redis essentials.

## 📚 Learning Objectives

By the end of this week, you will:
- Understand **why** caching is critical for modern applications
- Know the fundamentals of Redis data structures
- Implement practical caching patterns
- Build 3 real-world mini-projects

---

## 📖 Theory Section

Navigate to the [theory folder](./theory/) for detailed explanations:
- [Why Caching Matters](./theory/01-why-caching-matters.md)
- [Redis Core Concepts](./theory/02-redis-core-concepts.md)
- [TTL and Eviction Policies](./theory/03-ttl-and-eviction.md)
- [Use Cases for Backend Engineers](./theory/04-use-cases.md)

---

## 🛠 Hands-On Projects

### Setup
Start here: [Setup Redis with Docker](./hands-on/setup/)

### Mini-Projects
1. **[Cache a Slow API](./hands-on/mini-projects/cache-api/)** (Port 8000)
   - Cache-aside pattern with Redis Strings
   - 40-500x performance improvement
   - TTL-based expiration

2. **[Rate Limiter](./hands-on/mini-projects/rate-limiter/)** (Port 8001)
   - Fixed window rate limiting with Redis INCR
   - Atomic operations
   - FastAPI dependency injection

3. **[Session Storage](./hands-on/mini-projects/session-storage/)** (Port 8002)
   - Redis Hashes for structured data
   - Cookie-based authentication
   - Sliding window TTL

---

## 🎯 Daily Schedule (Suggested)

### Day 1: Theory + Setup
- Read theory materials (1-2 hours)
- Install Redis with Docker
- Explore Redis CLI commands

### Day 2-3: Cache API Project
- Build the slow API caching layer
- Experiment with different TTL values
- Compare cached vs non-cached performance

### Day 4: Rate Limiter
- Implement rate limiting with Redis INCR
- Test with multiple requests
- Understand atomic operations

### Day 5: Session Storage
- Build session management with Hashes
- Test login/logout flow
- Understand cookie-based auth

---

## 📋 Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Basic understanding of HTTP APIs

---

## 🚀 Quick Start

```bash
# 1. Start Redis
cd hands-on/setup
docker-compose up -d

# 2. Run first mini-project
cd ../mini-projects/cache-api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Visit **http://localhost:8000/docs** for the API documentation.
