"""
Redis client manager
"""

import redis
import os


class RedisClient:
    """Redis connection manager"""
    
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except:
            return False
    
    def get_client(self):
        """Get the underlying Redis client"""
        return self.client


# Global Redis client instance
redis_client = RedisClient()

