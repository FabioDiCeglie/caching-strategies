# Database Caching with Redis

Blog API demonstrating **Cache-Aside pattern** with Postgres + Redis.

## 🎯 What You'll Learn

- Cache-Aside (Lazy Loading) pattern
- Cache invalidation on writes
- Real performance differences at scale (500k records)
- Production-ready Docker setup

## 🚀 Quick Start

**Prerequisites:** Docker

```bash
# Start everything (Postgres + Redis + FastAPI)
./start.sh

# Run performance tests (in another terminal)
docker exec -it blog-api python test_performance.py

# Stop everything and clean all data
./stop.sh
```

## 📊 API Endpoints

- `GET /posts` - Get all posts (cache demo with 500k records)
- `GET /posts/{id}` - Get single post
- `POST /posts` - Create post (invalidates cache)
- `PUT /posts/{id}` - Update post (invalidates cache)
- `DELETE /posts/{id}` - Delete post (invalidates cache)
- `GET /health` - Health check

**API Docs:** http://localhost:8003/docs

## 🧪 What to Expect

**GET /posts (500,000 records):**
- First request (cache miss): ~10 seconds
- Second request (cache hit): ~3 seconds
- **3.5x faster with cache!**

**GET /posts/123 (single record):**
- First request (cache miss): ~10-20ms
- Second request (cache hit): ~1-2ms
- **10x faster with cache!**

**POST /posts:**
- Invalidates `post:all` cache
- Next GET will be cache miss (fresh data)

## 🔑 Key Concepts

### Cache-Aside Pattern

**On READ:**
1. Check Redis first
2. If MISS → Query database → Store in Redis
3. If HIT → Return from Redis

**On WRITE:**
1. Update database
2. Invalidate cache
3. Next read fetches fresh data

### Why This Matters

- Single record caching: **10x faster** (database → Redis)
- Large datasets: **3-5x faster** (limited by JSON serialization)
- Production systems use **pagination** to cache small chunks

## 🐳 Docker Services

- **postgres-blog-api** - PostgreSQL database (port 5432)
- **redis-blog-api** - Redis cache (port 6379)
- **blog-api** - FastAPI application (port 8003)

## 🛠️ Development

**View logs:**
```bash
docker compose logs -f app
```

**Access Redis CLI:**
```bash
docker exec -it redis-blog-api redis-cli
> KEYS post:*
> GET post:1
> TTL post:all
```

**Access Postgres:**
```bash
docker exec -it postgres-blog-api psql -U blog_user -d blog_db
# \dt - list tables
# SELECT COUNT(*) FROM posts;
```

## 📁 Project Structure

```
.
├── main.py              # FastAPI application
├── database.py          # SQLAlchemy models & connection
├── cache.py             # Redis cache layer
├── test_performance.py  # Performance testing script
├── docker-compose.yml   # All services
├── Dockerfile           # FastAPI app image
├── requirements.txt     # Python dependencies
├── start.sh             # Start script
└── stop.sh              # Stop script
```

## 💡 Next Steps

- Add pagination to `/posts` endpoint
- Implement cache warming strategies
- Add monitoring/metrics (Prometheus)
- Try Write-Through pattern instead of invalidation
- Experiment with different TTL values

