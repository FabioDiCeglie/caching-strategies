"""
Redis distributed lock implementation
"""

import time
import uuid
from redis_client import RedisClient


class RedisLock:
    """Simple distributed lock using Redis"""
    
    def __init__(self, redis_client: RedisClient):
        self.client = redis_client.get_client()
        self.lock_id = None
    
    def acquire(self, key: str, timeout: int = 10) -> bool:
        """
        Acquire a lock
        
        Args:
            key: Lock key (e.g., "lock:event:1")
            timeout: Lock expiration time in seconds
        
        Returns:
            True if lock acquired, False otherwise
        """
        # Generate unique lock ID
        self.lock_id = str(uuid.uuid4())
        
        # Try to set the key with NX (only if not exists) and EX (expiration)
        # This is atomic in Redis
        result = self.client.set(
            key,
            self.lock_id,
            nx=True,  # Only set if key doesn't exist
            ex=timeout  # Expire after timeout seconds
        )
        
        if result:
            print(f"🔒 Lock acquired: {key} (ID: {self.lock_id[:8]}...)")
            return True
        else:
            print(f"⏳ Lock busy: {key}")
            return False
    
    def release(self, key: str) -> bool:
        """
        Release a lock (only if we own it)
        
        Uses Lua script to ensure atomicity:
        - Check if lock value matches our lock_id
        - Delete only if it matches
        """
        if not self.lock_id:
            return False
        
        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.client.eval(lua_script, 1, key, self.lock_id)
        
        if result:
            print(f"🔓 Lock released: {key}")
            return True
        else:
            print(f"⚠️  Lock not owned or expired: {key}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass


def with_lock(key: str, timeout: int = 10, wait_time: int = 5):
    """
    Decorator for using Redis lock
    
    Args:
        key: Lock key
        timeout: Lock expiration (safety net)
        wait_time: How long to wait for lock
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            from redis_client import redis_client
            lock = RedisLock(redis_client)
            
            # Try to acquire lock with retries
            start_time = time.time()
            while time.time() - start_time < wait_time:
                if lock.acquire(key, timeout):
                    try:
                        # Execute function while holding lock
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        lock.release(key)
                
                # Wait a bit before retrying
                time.sleep(0.1)
            
            # Couldn't acquire lock
            raise Exception(f"Could not acquire lock: {key}")
        
        return wrapper
    return decorator

