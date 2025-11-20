"""
Blog API with Database + Redis Caching

Pattern: Cache-Aside (Lazy Loading) with Explicit Invalidation
This is the most common pattern in real-world applications!
- READ: Check cache first → MISS → Query DB → Store in cache
- WRITE: Update DB → Invalidate cache → Next read fetches fresh data
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from contextlib import asynccontextmanager
import time

from database import get_db, init_db, seed_data, Post
from cache import cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and Redis on startup"""
    init_db()
    seed_data()
    
    if cache.ping():
        print("✅ Redis connected")
    else:
        print("⚠️  Redis not connected - caching disabled")
    
    yield


app = FastAPI(
    title="Blog API with Redis Caching",
    description="Demonstrates caching patterns with real database",
    version="1.0.0",
    lifespan=lifespan
)


class PostCreate(BaseModel):
    title: str
    content: str
    author: str


class PostUpdate(BaseModel):
    title: str = None
    content: str = None
    author: str = None


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: str
    updated_at: str
    cached: bool = False


@app.get("/posts", response_model=List[PostResponse])
async def get_all_posts(db: Session = Depends(get_db)):
    """Get all posts with caching"""
    start_time = time.time()
    
    cached_posts = cache.get_all_posts()
    
    if cached_posts:
        duration = (time.time() - start_time) * 1000
        print(f"✅ Cache HIT - All posts ({duration:.2f}ms)")
        
        for post in cached_posts:
            post['cached'] = True
        return cached_posts
    
    print(f"❌ Cache MISS - Querying database")
    posts = db.query(Post).all()
    posts_data = [post.to_dict() for post in posts]
    
    cache.set_all_posts(posts_data, ttl=300)
    
    duration = (time.time() - start_time) * 1000
    print(f"📊 Database query took {duration:.2f}ms")
    
    return posts_data


@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get single post with caching (cache-aside pattern)"""
    start_time = time.time()
    
    cached_post = cache.get_post(post_id)
    
    if cached_post:
        duration = (time.time() - start_time) * 1000
        print(f"✅ Cache HIT - Post {post_id} ({duration:.2f}ms)")
        cached_post['cached'] = True
        return cached_post
    
    print(f"❌ Cache MISS - Querying database for post {post_id}")
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_data = post.to_dict()
    cache.set_post(post_id, post_data, ttl=300)
    
    duration = (time.time() - start_time) * 1000
    print(f"📊 Database query took {duration:.2f}ms")
    
    return post_data


@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create new post and invalidate cache"""
    new_post = Post(
        title=post.title,
        content=post.content,
        author=post.author
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    cache.delete_pattern("post:all")
    print(f"🔄 Cache invalidated - Created post {new_post.id}")
    
    return new_post.to_dict()


@app.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post_update: PostUpdate, db: Session = Depends(get_db)):
    """Update post and invalidate cache"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post_update.title:
        post.title = post_update.title
    if post_update.content:
        post.content = post_update.content
    if post_update.author:
        post.author = post_update.author
    
    db.commit()
    db.refresh(post)
    
    cache.delete_post(post_id)
    cache.delete_pattern("post:all")
    print(f"🔄 Cache invalidated - Updated post {post_id}")
    
    return post.to_dict()


@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete post and invalidate cache"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    
    cache.delete_post(post_id)
    cache.delete_pattern("post:all")
    print(f"🔄 Cache invalidated - Deleted post {post_id}")
    
    return None


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if cache.ping() else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Blog API with Redis Caching...")
    print("📚 API docs: http://localhost:8003/docs")
    uvicorn.run(app, host="0.0.0.0", port=8003)

