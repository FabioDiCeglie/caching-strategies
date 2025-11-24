# Week 2 — Redis in Real Backends

⭐ **Goal**: Apply Redis patterns to real-world backend systems with production-grade caching, invalidation, and distributed coordination.

## 📚 Learning Objectives

By the end of this week, you will:
- Understand caching patterns (Cache-Aside, Write-Through, etc.)
- Master cache invalidation strategies
- Implement distributed locks to prevent race conditions
- Build 3 production-ready projects with Docker

---

## 📖 Theory Section

Navigate to the [theory folder](./theory/) for detailed explanations:
- [Caching Patterns](./theory/01-caching-patterns.md)
- [Cache Invalidation Strategies](./theory/02-cache-invalidation.md)
- [Distributed Locks](./theory/03-distributed-locks.md)

---

## 🛠️ Hands-On Projects

### Project 1: [Database Caching](./hands-on/db-caching/)
- Cache-Aside pattern with 500,000 blog posts
- PostgreSQL + Redis + FastAPI
- 3-10x performance improvement
- Explicit cache invalidation

### Project 2: [Cache Invalidation Strategies](./hands-on/invalidation/)
- 7 invalidation strategies in one project
- TTL, Explicit, Write-Through, Event-Based, SWR, Tags, Combined
- Redis Pub/Sub with background worker
- Product catalog example

### Project 3: [Distributed Locks](./hands-on/locking/)
- Prevent race conditions in concurrent systems
- Redis SET NX PX for atomic locks
- Event booking with overselling protection
- Compare locked vs unlocked behavior

---

## 🎯 Daily Schedule (Suggested)

### Day 1-2: Theory + DB Caching
- Read caching patterns theory
- Build db-caching project
- Test with 500k records
- Compare cache hit vs miss performance

### Day 3-4: Cache Invalidation
- Read invalidation theory
- Build invalidation project
- Test all 7 strategies
- Run the Pub/Sub worker

### Day 5-6: Distributed Locks
- Read distributed locks theory
- Build locking project
- Test concurrent scenarios
- Understand race conditions

### Day 7: Review & Experiment
- Compare all three projects
- Combine patterns (caching + locks)
- Add your own endpoints
- Experiment with different TTL values

---

## 📋 Prerequisites

- Python 3.8+
- Docker & Docker Compose
- PostgreSQL knowledge (basic)
- Understanding of Week 1 concepts

---

## 🚀 Quick Start

```bash
# Project 1: Database Caching
cd hands-on/db-caching
./start.sh
docker exec -it blog-api python test_performance.py

# Project 2: Cache Invalidation
cd ../invalidation
./start.sh
docker exec -it shop-api python test_strategies.py

# Project 3: Distributed Locks
cd ../locking
./start.sh
docker exec -it booking-api python test_concurrent.py
```

---

## 💡 Key Takeaways

**Caching Patterns:**
- Cache-Aside is 90% of real-world usage
- Always set TTL even with explicit invalidation
- Cache at the right layer for maximum benefit

**Invalidation Strategies:**
- TTL: Simple but eventual consistency
- Explicit: Immediate but next read is slow
- Write-Through: Best for read-heavy workloads
- Event-Based: Essential for microservices
- Production systems combine multiple strategies

**Distributed Locks:**
- Use for ANY concurrent writes to shared resources
- Always set TTL as safety net for crashes
- Keep critical sections short
- Race conditions are rare but catastrophic

