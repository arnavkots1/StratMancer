"""
Caching service with Redis and in-memory fallback
"""

import json
import hashlib
import logging
from typing import Optional, Any
from functools import lru_cache
import time

from backend.config import settings

logger = logging.getLogger(__name__)


# Try to import Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("Redis not installed. Using in-memory cache only.")


class CacheService:
    """Cache service with Redis and in-memory fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # key -> (value, expiry_time)
        
        if settings.USE_REDIS and HAS_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self.redis_client = None
        else:
            logger.info("Using in-memory cache (Redis disabled)")
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        # Convert data to JSON string and hash it
        json_str = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(json_str.encode()).hexdigest()
        return f"{prefix}:{hash_val}"
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if time.time() < expiry:
                logger.debug(f"Cache HIT (memory): {key}")
                return value
            else:
                # Expired
                del self.memory_cache[key]
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, value)
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to memory cache
        expiry = time.time() + ttl
        self.memory_cache[key] = (value, expiry)
        logger.debug(f"Cache SET (memory): {key} (TTL: {ttl}s)")
        
        # Clean expired entries periodically
        self._clean_memory_cache()
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        deleted = False
        
        # Try Redis
        if self.redis_client:
            try:
                deleted = self.redis_client.delete(key) > 0
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Also delete from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True
        
        return deleted
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        # Clear Redis
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Clear memory cache
        self.memory_cache.clear()
        logger.info("Cache cleared")
        return True
    
    def _clean_memory_cache(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.memory_cache.items()
            if current_time >= expiry
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def get_prediction(self, request_data: dict) -> Optional[dict]:
        """Get cached prediction"""
        key = self._generate_key("prediction", request_data)
        cached = await self.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    async def set_prediction(self, request_data: dict, response_data: dict, ttl: int = None):
        """Cache prediction result"""
        key = self._generate_key("prediction", request_data)
        await self.set(key, json.dumps(response_data), ttl)


# Global cache instance
cache_service = CacheService()

