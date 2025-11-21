"""
Cache manager implementing multiple invalidation strategies
"""

import redis
import json
import os
import time
from typing import Optional
from datetime import datetime


class CacheManager:
    """Redis cache with multiple invalidation strategies"""
    
    def __init__(self, host='localhost', port=6379):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True
        )
    
    # ==========================================
    # Strategy 1: TTL (Time To Live)
    # ==========================================
    
    def set_with_ttl(self, key: str, value: dict, ttl: int):
        """Cache with automatic expiration"""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            print(f"✅ [TTL] Cached {key} for {ttl} seconds")
        except Exception as e:
            print(f"❌ Cache set error: {e}")
    
    def get_with_ttl(self, key: str) -> Optional[dict]:
        """Get cached value and show remaining TTL"""
        try:
            value = self.client.get(key)
            if value:
                ttl = self.client.ttl(key)
                print(f"✅ [TTL] Cache HIT - {key} (expires in {ttl}s)")
                return json.loads(value)
            print(f"❌ [TTL] Cache MISS - {key}")
            return None
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            return None
    
    # ==========================================
    # Strategy 2: Explicit Invalidation
    # ==========================================
    
    def invalidate_explicit(self, key: str):
        """Delete cache entry immediately"""
        try:
            deleted = self.client.delete(key)
            if deleted:
                print(f"🗑️  [EXPLICIT] Invalidated {key}")
            else:
                print(f"⚠️  [EXPLICIT] Key {key} not found")
        except Exception as e:
            print(f"❌ Cache delete error: {e}")
    
    # ==========================================
    # Strategy 3: Write-Through
    # ==========================================
    
    def update_write_through(self, key: str, value: dict, ttl: int = 300):
        """Update cache with new data (after DB write)"""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            print(f"✏️  [WRITE-THROUGH] Updated cache {key}")
        except Exception as e:
            print(f"❌ Cache update error: {e}")
    
    # ==========================================
    # Strategy 4: Event-Based Invalidation
    # ==========================================
    
    def publish_invalidation_event(self, channel: str, data: dict):
        """Publish invalidation event to channel"""
        try:
            self.client.publish(channel, json.dumps(data))
            print(f"📢 [EVENT-BASED] Published to {channel}: {data}")
        except Exception as e:
            print(f"❌ Publish error: {e}")
    
    def subscribe_to_events(self, channel: str):
        """Subscribe to invalidation events (for background worker)"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    # ==========================================
    # Strategy 5: SWR (Stale-While-Revalidate)
    # ==========================================
    
    def get_with_swr(self, key: str, stale_threshold: int = 30) -> tuple[Optional[dict], bool]:
        """
        Get cached value with SWR pattern
        Returns: (value, needs_refresh)
        """
        try:
            value = self.client.get(key)
            if value:
                ttl = self.client.ttl(key)
                
                # If TTL is low, return stale data but signal refresh needed
                if 0 < ttl < stale_threshold:
                    print(f"⚡ [SWR] Cache HIT (stale) - {key} (TTL: {ttl}s) - needs refresh")
                    return json.loads(value), True  # Stale, needs refresh
                elif ttl > 0:
                    print(f"✅ [SWR] Cache HIT (fresh) - {key} (TTL: {ttl}s)")
                    return json.loads(value), False  # Fresh, no refresh needed
            
            print(f"❌ [SWR] Cache MISS - {key}")
            return None, True  # No cache, needs refresh
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            return None, True
    
    def refresh_swr(self, key: str, value: dict, ttl: int):
        """Refresh cache in background (SWR pattern)"""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            print(f"🔄 [SWR] Refreshed cache {key} in background")
        except Exception as e:
            print(f"❌ Cache refresh error: {e}")
    
    # ==========================================
    # Strategy 6: Cache Tags
    # ==========================================
    
    def set_with_tags(self, key: str, value: dict, tags: list[str], ttl: int = 300):
        """Cache with tags for group invalidation"""
        try:
            # Store the value
            self.client.setex(key, ttl, json.dumps(value))
            
            # Add key to tag sets
            for tag in tags:
                self.client.sadd(f"tag:{tag}", key)
                # Set TTL on tag set (slightly longer than data)
                self.client.expire(f"tag:{tag}", ttl + 60)
            
            print(f"🏷️  [TAGS] Cached {key} with tags: {tags}")
        except Exception as e:
            print(f"❌ Cache set with tags error: {e}")
    
    def invalidate_by_tag(self, tag: str):
        """Invalidate all cache entries with a specific tag"""
        try:
            # Get all keys with this tag
            keys = self.client.smembers(f"tag:{tag}")
            
            if keys:
                # Delete all keys
                self.client.delete(*keys)
                # Delete the tag set itself
                self.client.delete(f"tag:{tag}")
                print(f"🏷️  [TAGS] Invalidated {len(keys)} entries with tag: {tag}")
            else:
                print(f"⚠️  [TAGS] No entries found with tag: {tag}")
        except Exception as e:
            print(f"❌ Tag invalidation error: {e}")
    
    # ==========================================
    # Strategy 7: Combined (Production Pattern)
    # ==========================================
    
    def set_combined(self, key: str, value: dict, tags: list[str] = None, ttl: int = 300):
        """
        Combined strategy: Write-Through + TTL + Tags
        This is how production systems do it
        """
        try:
            # Store with TTL (safety net)
            self.client.setex(key, ttl, json.dumps(value))
            
            # Add tags if provided
            if tags:
                for tag in tags:
                    self.client.sadd(f"tag:{tag}", key)
                    self.client.expire(f"tag:{tag}", ttl + 60)
            
            print(f"🔥 [COMBINED] Cached {key} (TTL: {ttl}s, Tags: {tags or 'none'})")
        except Exception as e:
            print(f"❌ Combined cache error: {e}")
    
    def invalidate_combined(self, key: str, event_channel: str = None):
        """
        Combined invalidation: Explicit + Event-Based
        """
        try:
            # Delete the key
            self.client.delete(key)
            
            # Publish event if channel provided
            if event_channel:
                self.publish_invalidation_event(event_channel, {"key": key})
            
            print(f"🔥 [COMBINED] Invalidated {key}" + (f" + published event" if event_channel else ""))
        except Exception as e:
            print(f"❌ Combined invalidation error: {e}")
    
    # ==========================================
    # Utility Methods
    # ==========================================
    
    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except:
            return False
    
    def get_stats(self, key: str):
        """Get cache statistics for a key"""
        try:
            exists = self.client.exists(key)
            if exists:
                ttl = self.client.ttl(key)
                return {
                    "exists": True,
                    "ttl": ttl,
                    "expires_in": f"{ttl} seconds" if ttl > 0 else "no expiration"
                }
            return {"exists": False}
        except Exception as e:
            return {"error": str(e)}


cache = CacheManager(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379))
)

