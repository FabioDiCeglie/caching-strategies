"""
Product Catalog API demonstrating 7 cache invalidation strategies

Each endpoint shows a different strategy in action
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import time

from database import get_db, init_db, seed_data, Product, Category
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
    title="Cache Invalidation Strategies Demo",
    description="7 different cache invalidation patterns",
    version="1.0.0",
    lifespan=lifespan
)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category_id: int
    category_name: Optional[str]
    featured: bool
    cached: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


# ==========================================
# Strategy 1: TTL (Time To Live)
# Simple auto-expiration
# ==========================================

@app.get("/products/ttl/{product_id}", response_model=ProductResponse)
async def get_product_ttl(product_id: int, db: Session = Depends(get_db)):
    """
    Strategy 1: TTL-based caching
    - Cache expires automatically after 60 seconds
    - Good for: Data that can be slightly stale
    """
    key = f"product:ttl:{product_id}"
    
    # Try cache first
    cached = cache.get_with_ttl(key)
    if cached:
        cached['cached'] = True
        return cached
    
    # Cache miss - query database
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.to_dict()
    
    # Cache for 60 seconds
    cache.set_with_ttl(key, product_data, ttl=60)
    
    return product_data


# ==========================================
# Strategy 2: Explicit Invalidation
# Delete on write
# ==========================================

@app.get("/products/explicit/{product_id}", response_model=ProductResponse)
async def get_product_explicit(product_id: int, db: Session = Depends(get_db)):
    """
    Strategy 2: Explicit invalidation (get)
    - Cache until manually deleted
    - Deleted when product is updated/deleted
    """
    key = f"product:explicit:{product_id}"
    
    cached = cache.get_with_ttl(key)
    if cached:
        cached['cached'] = True
        return cached
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.to_dict()
    cache.set_with_ttl(key, product_data, ttl=3600)  # Long TTL
    
    return product_data


@app.delete("/products/explicit/{product_id}")
async def delete_product_explicit(product_id: int, db: Session = Depends(get_db)):
    """
    Strategy 2: Explicit invalidation (delete)
    - Removes product from DB
    - Explicitly deletes cache ( we do the same for UPDATE operations )
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    
    # Explicitly invalidate cache
    key = f"product:explicit:{product_id}"
    cache.invalidate_explicit(key)
    
    return {"message": "Product deleted and cache invalidated"}


# ==========================================
# Strategy 3: Write-Through
# Update cache on write
# ==========================================

@app.get("/products/writethrough/{product_id}", response_model=ProductResponse)
async def get_product_writethrough(product_id: int, db: Session = Depends(get_db)):
    """Strategy 3: Write-through (get)"""
    key = f"product:writethrough:{product_id}"
    
    cached = cache.get_with_ttl(key)
    if cached:
        cached['cached'] = True
        return cached
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.to_dict()
    cache.set_with_ttl(key, product_data, ttl=300)
    
    return product_data


@app.put("/products/writethrough/{product_id}", response_model=ProductResponse)
async def update_product_writethrough(
    product_id: int,
    update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Strategy 3: Write-through (update)
    - Updates database
    - Updates cache with new data (not delete!)
    - Next read is fast (cache hit)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update database
    if update.name:
        product.name = update.name
    if update.description:
        product.description = update.description
    if update.price:
        product.price = update.price
    
    db.commit()
    db.refresh(product)
    
    # Write-through: Update cache with new data
    key = f"product:writethrough:{product_id}"
    product_data = product.to_dict()
    cache.update_write_through(key, product_data, ttl=300)
    
    return product_data


# ==========================================
# Strategy 4: Event-Based Invalidation
# Pub/Sub pattern
# ==========================================

@app.get("/products/events/{product_id}", response_model=ProductResponse)
async def get_product_events(product_id: int, db: Session = Depends(get_db)):
    """Strategy 4: Event-based (get)"""
    key = f"product:events:{product_id}"
    
    cached = cache.get_with_ttl(key)
    if cached:
        cached['cached'] = True
        return cached
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.to_dict()
    cache.set_with_ttl(key, product_data, ttl=600)
    
    return product_data


@app.put("/products/events/{product_id}")
async def update_product_events(
    product_id: int,
    update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Strategy 4: Event-based invalidation
    - Updates database
    - Publishes event to Redis Pub/Sub
    - Subscribers invalidate their caches
    - Good for: Microservices architecture
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if update.name:
        product.name = update.name
    if update.description:
        product.description = update.description
    if update.price:
        product.price = update.price
    
    db.commit()
    
    # Publish invalidation event
    cache.publish_invalidation_event(
        "product:updates",
        {"product_id": product_id, "action": "update"}
    )
    
    # Also invalidate our own cache
    key = f"product:events:{product_id}"
    cache.invalidate_explicit(key)
    
    return {"message": "Product updated and event published"}


# ==========================================
# Strategy 5: SWR (Stale-While-Revalidate)
# Always fast, refresh in background
# ==========================================

@app.get("/products/featured", response_model=List[ProductResponse])
async def get_featured_products_swr(db: Session = Depends(get_db)):
    """
    Strategy 5: Stale-While-Revalidate (SWR)
    - Returns cached data immediately (even if stale)
    - Refreshes in background if TTL < 30s
    - Users always get fast response
    - Good for: High-traffic endpoints
    """
    key = "products:featured"
    
    # Check cache with SWR
    cached, needs_refresh = cache.get_with_swr(key, stale_threshold=30)
    
    if cached:
        # Return stale data immediately
        for item in cached:
            item['cached'] = True
        
        # If needs refresh, do it in background (simplified - normally async)
        if needs_refresh:
            print("🔄 [SWR] Background refresh triggered...")
            featured = db.query(Product).filter(Product.featured == 1).all()
            products_data = [p.to_dict() for p in featured]
            cache.refresh_swr(key, products_data, ttl=120)
        
        return cached
    
    # Cache miss - fetch and cache
    featured = db.query(Product).filter(Product.featured == 1).all()
    products_data = [p.to_dict() for p in featured]
    
    cache.set_with_ttl(key, products_data, ttl=120)
    
    return products_data


# ==========================================
# Strategy 6: Cache Tags
# Group invalidation
# ==========================================

@app.get("/products/by-category/{category_id}", response_model=List[ProductResponse])
async def get_products_by_category_tags(category_id: int, db: Session = Depends(get_db)):
    """
    Strategy 6: Cache Tags (get)
    - Products cached with category tag
    - Can invalidate all products in a category at once
    """
    key = f"products:category:{category_id}"
    
    cached = cache.get_with_ttl(key)
    if cached:
        for item in cached:
            item['cached'] = True
        return cached
    
    products = db.query(Product).filter(Product.category_id == category_id).all()
    products_data = [p.to_dict() for p in products]
    
    # Cache with tags
    cache.set_with_tags(
        key,
        products_data,
        tags=[f"category:{category_id}"],
        ttl=300
    )
    
    return products_data


@app.put("/categories/{category_id}")
async def update_category_tags(category_id: int, db: Session = Depends(get_db)):
    """
    Strategy 6: Cache Tags (invalidate)
    - Updates category
    - Invalidates ALL products in that category
    - One operation clears many cache entries
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Invalidate all products with this category tag
    cache.invalidate_by_tag(f"category:{category_id}")
    
    return {"message": f"Category updated, all related products invalidated"}


# ==========================================
# Strategy 7: Combined (Production Pattern)
# TTL + Tags + Events
# ==========================================

@app.get("/products/production/{product_id}", response_model=ProductResponse)
async def get_product_production(product_id: int, db: Session = Depends(get_db)):
    """
    Strategy 7: Combined (Production pattern)
    - Uses TTL as safety net
    - Uses tags for group invalidation
    - Uses events for distributed systems
    - This is how REAL systems do it!
    """
    key = f"product:production:{product_id}"
    
    cached = cache.get_with_ttl(key)
    if cached:
        cached['cached'] = True
        return cached
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_data = product.to_dict()
    
    # Combined: TTL + Tags
    cache.set_combined(
        key,
        product_data,
        tags=[f"category:{product.category_id}", "all_products"],
        ttl=300
    )
    
    return product_data


@app.put("/products/production/{product_id}")
async def update_product_production(
    product_id: int,
    update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Strategy 7: Combined invalidation
    - Updates database
    - Invalidates cache explicitly
    - Publishes event for other services
    - Combines best of all strategies
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if update.name:
        product.name = update.name
    if update.description:
        product.description = update.description
    if update.price:
        product.price = update.price
    
    db.commit()
    
    # Combined invalidation: Explicit + Event
    key = f"product:production:{product_id}"
    cache.invalidate_combined(key, event_channel="product:updates")
    
    # Also invalidate by tags
    cache.invalidate_by_tag(f"category:{product.category_id}")
    
    return {"message": "Product updated using production strategy"}


# ==========================================
# Utility Endpoints
# ==========================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if cache.ping() else "disconnected"
    }


@app.get("/cache/stats/{key}")
async def get_cache_stats(key: str):
    """Get cache statistics for a key"""
    return cache.get_stats(key)


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Cache Invalidation Demo API...")
    print("📚 API docs: http://localhost:8004/docs")
    uvicorn.run(app, host="0.0.0.0", port=8004)

