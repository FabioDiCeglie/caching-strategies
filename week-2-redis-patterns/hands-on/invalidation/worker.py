"""
Simple worker that subscribes to Redis Pub/Sub events
Demonstrates how other services would listen and react to cache invalidation events
"""

import json
from datetime import datetime
from cache import cache


def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def main():
    """Subscribe to product update events"""
    
    log("🎧 Worker started - Simulating Service B (separate microservice)")
    log("📡 Subscribed to channel: product:updates")
    log("💡 This worker represents a DIFFERENT service invalidating its own cache")
    log("=" * 60)
    
    # Subscribe to the channel using cache manager
    pubsub = cache.subscribe_to_events('product:updates')
    
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                
                log("📢 EVENT RECEIVED!")
                log(f"   Channel: {message['channel']}")
                log(f"   Data: {data}")
                
                # React to event - invalidate THIS service's cache
                product_id = data.get('product_id')
                key = data.get('key')
                action = data.get('action', 'update')
                
                log(f"   Action: {action}")
                
                if product_id:
                    # Service B invalidates its own cached copy
                    # (could be different key namespace like "serviceB:product:X")
                    cache_key = f"product:events:{product_id}"
                    cache.invalidate_explicit(cache_key)
                    log(f"   🗑️  Service B invalidated its cache: {cache_key}")
                    log(f"   💡 Note: Service A already invalidated its own cache")
                elif key:
                    # Invalidate specific key passed in event
                    cache.invalidate_explicit(key)
                    log(f"   🗑️  Service B invalidated its cache: {key}")
                
                log("=" * 60)
    
    except KeyboardInterrupt:
        log("\n👋 Worker stopped")
        pubsub.unsubscribe()


if __name__ == "__main__":
    main()

