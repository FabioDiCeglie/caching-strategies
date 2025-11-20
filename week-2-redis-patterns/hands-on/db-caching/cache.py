"""
Cache layer with Redis
Implements cache-aside pattern
"""

import redis
import json
from typing import Optional


class RedisCache:
    """Redis cache manager with cache-aside pattern"""
    
    def __init__(self, host='localhost', port=6379, default_ttl=300):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[dict]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: dict, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
    
    def ping(self) -> bool:
        """Check if Redis is connected"""
        try:
            return self.client.ping()
        except:
            return False


class PostCache(RedisCache):
    """Cache manager specifically for blog posts"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = "post"
    
    def get_post(self, post_id: int) -> Optional[dict]:
        """Get single post from cache"""
        key = f"{self.prefix}:{post_id}"
        return self.get(key)
    
    def set_post(self, post_id: int, post_data: dict, ttl: Optional[int] = None):
        """Cache single post"""
        key = f"{self.prefix}:{post_id}"
        self.set(key, post_data, ttl)
    
    def delete_post(self, post_id: int):
        """Remove post from cache"""
        key = f"{self.prefix}:{post_id}"
        self.delete(key)
    
    def get_all_posts(self) -> Optional[list]:
        """Get all posts list from cache"""
        key = f"{self.prefix}:all"
        return self.get(key)
    
    def set_all_posts(self, posts_data: list, ttl: Optional[int] = None):
        """Cache all posts list"""
        key = f"{self.prefix}:all"
        self.set(key, posts_data, ttl)
    
    def invalidate_all(self):
        """Invalidate all post-related caches"""
        self.delete_pattern(f"{self.prefix}:*")


cache = PostCache()

