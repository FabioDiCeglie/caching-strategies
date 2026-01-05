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

Each project includes Redis + FastAPI in Docker — just run `./start.sh`!

| Project | Port | Key Concepts |
|---------|------|--------------|
| [Cache a Slow API](./hands-on/mini-projects/cache-api/) | 8000 | Cache-aside, TTL, Strings |
| [Rate Limiter](./hands-on/mini-projects/rate-limiter/) | 8001 | INCR, atomic ops, fixed window |
| [Session Storage](./hands-on/mini-projects/session-storage/) | 8002 | Hashes, cookies, sliding TTL |

---

## 🚀 Quick Start

```bash
# Pick any project and run
cd hands-on/mini-projects/cache-api
./start.sh

# Stop when done
./stop.sh
```

Visit **http://localhost:8000/docs** for the API documentation.

---

## 📋 Prerequisites

- Docker & Docker Compose
- Basic understanding of HTTP APIs
