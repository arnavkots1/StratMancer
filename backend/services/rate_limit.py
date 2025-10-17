"""
Advanced rate limiting with Redis-based token bucket algorithm.
Falls back to in-memory implementation if Redis is unavailable.
"""

import time
import logging
from typing import Optional, Tuple
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("Redis not installed. Using in-memory rate limiter.")


class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            Tuple of (success, retry_after_seconds)
        """
        with self.lock:
            now = time.time()
            
            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_refill = now
            
            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            else:
                # Calculate retry after time
                tokens_needed = tokens - self.tokens
                retry_after = tokens_needed / self.refill_rate
                return False, retry_after


class RedisTokenBucket:
    """Redis-backed token bucket for distributed rate limiting"""
    
    def __init__(self, redis_client, key_prefix: str, capacity: int, refill_rate: float):
        """
        Initialize Redis token bucket.
        
        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
            capacity: Maximum tokens
            refill_rate: Tokens per second
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate
    
    def consume(self, identifier: str, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to consume tokens using Redis.
        
        Uses Lua script for atomic operations.
        
        Args:
            identifier: Unique identifier (IP, API key, etc.)
            tokens: Number of tokens to consume
        
        Returns:
            Tuple of (success, retry_after_seconds)
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        
        # Lua script for atomic token bucket operations
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_to_consume = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        -- Get current state
        local state = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(state[1]) or capacity
        local last_refill = tonumber(state[2]) or now
        
        -- Refill tokens
        local time_passed = now - last_refill
        tokens = math.min(capacity, tokens + time_passed * refill_rate)
        
        -- Try to consume
        if tokens >= tokens_to_consume then
            tokens = tokens - tokens_to_consume
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)  -- Expire after 1 hour
            return {1, 0}  -- success, retry_after
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            local tokens_needed = tokens_to_consume - tokens
            local retry_after = tokens_needed / refill_rate
            return {0, retry_after}
        end
        """
        
        try:
            result = self.redis.eval(
                lua_script,
                1,
                key,
                self.capacity,
                self.refill_rate,
                tokens,
                now
            )
            
            success = result[0] == 1
            retry_after = float(result[1])
            
            return success, retry_after
        
        except Exception as e:
            logger.error(f"Redis token bucket error: {e}")
            # On error, allow the request (fail open)
            return True, 0.0


class RateLimiter:
    """
    Multi-tier rate limiter with Redis backend and in-memory fallback.
    
    Three tiers:
    - Per-IP: 60 requests/minute
    - Per-API-Key: 600 requests/minute
    - Global: 3000 requests/minute
    """
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        use_redis: bool = False
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            use_redis: Whether to use Redis (falls back to memory if unavailable)
        """
        self.use_redis = use_redis and HAS_REDIS
        self.redis_client = None
        
        # Rate limit configurations (capacity, refill_rate per second)
        self.limits = {
            'per_ip': (60, 1.0),        # 60 req/min = 1 req/sec
            'per_key': (600, 10.0),     # 600 req/min = 10 req/sec
            'global': (3000, 50.0)      # 3000 req/min = 50 req/sec
        }
        
        # Try to connect to Redis
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=False,  # We handle encoding in Lua
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                self.redis_client.ping()
                logger.info(f"Rate limiter using Redis: {redis_host}:{redis_port}")
                
                # Create Redis token buckets
                self.buckets = {
                    'per_ip': RedisTokenBucket(
                        self.redis_client,
                        'ratelimit:ip',
                        *self.limits['per_ip']
                    ),
                    'per_key': RedisTokenBucket(
                        self.redis_client,
                        'ratelimit:key',
                        *self.limits['per_key']
                    ),
                    'global': RedisTokenBucket(
                        self.redis_client,
                        'ratelimit:global',
                        *self.limits['global']
                    )
                }
                self.using_redis = True
            
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory rate limiter.")
                self._setup_memory_buckets()
                self.using_redis = False
        else:
            logger.info("Rate limiter using in-memory buckets")
            self._setup_memory_buckets()
            self.using_redis = False
    
    def _setup_memory_buckets(self):
        """Setup in-memory token buckets"""
        self.memory_buckets = {
            'per_ip': defaultdict(lambda: TokenBucket(*self.limits['per_ip'])),
            'per_key': defaultdict(lambda: TokenBucket(*self.limits['per_key'])),
            'global': TokenBucket(*self.limits['global'])
        }
        self.using_redis = False
    
    def check_rate_limit(
        self,
        ip: str,
        api_key: Optional[str] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if request should be rate limited.
        
        Checks all three tiers and returns first violation.
        
        Args:
            ip: Client IP address
            api_key: API key (if authenticated)
        
        Returns:
            Tuple of (allowed, limit_type, retry_after_seconds)
        """
        # Check global limit first (most restrictive)
        if self.using_redis:
            allowed, retry_after = self.buckets['global'].consume('global')
        else:
            allowed, retry_after = self.memory_buckets['global'].consume()
        
        if not allowed:
            return False, 'global', retry_after
        
        # Check per-IP limit
        if self.using_redis:
            allowed, retry_after = self.buckets['per_ip'].consume(ip)
        else:
            allowed, retry_after = self.memory_buckets['per_ip'][ip].consume()
        
        if not allowed:
            return False, 'per_ip', retry_after
        
        # Check per-key limit (if API key provided)
        if api_key:
            if self.using_redis:
                allowed, retry_after = self.buckets['per_key'].consume(api_key)
            else:
                allowed, retry_after = self.memory_buckets['per_key'][api_key].consume()
            
            if not allowed:
                return False, 'per_key', retry_after
        
        # All checks passed
        return True, None, 0.0
    
    def get_limit_info(self, limit_type: str) -> dict:
        """Get information about a specific limit"""
        capacity, refill_rate = self.limits[limit_type]
        return {
            'capacity': capacity,
            'refill_rate_per_second': refill_rate,
            'refill_rate_per_minute': refill_rate * 60,
            'backend': 'redis' if self.using_redis else 'memory'
        }
    
    def reset_limits(self, identifier: Optional[str] = None):
        """
        Reset rate limits (for testing).
        
        Args:
            identifier: Specific identifier to reset (IP or key), or None for all
        """
        if self.using_redis and self.redis_client:
            if identifier:
                # Reset specific identifier
                for prefix in ['ip', 'key']:
                    key = f"ratelimit:{prefix}:{identifier}"
                    self.redis_client.delete(key)
            else:
                # Reset all
                for key in self.redis_client.scan_iter("ratelimit:*"):
                    self.redis_client.delete(key)
        else:
            # Reset in-memory buckets
            if identifier:
                for bucket_type in ['per_ip', 'per_key']:
                    if identifier in self.memory_buckets[bucket_type]:
                        del self.memory_buckets[bucket_type][identifier]
            else:
                # Reset all
                self._setup_memory_buckets()


# Global rate limiter instance (will be initialized by main app)
rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return rate_limiter


def init_rate_limiter(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    use_redis: bool = False
):
    """Initialize global rate limiter"""
    global rate_limiter
    rate_limiter = RateLimiter(
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db,
        use_redis=use_redis
    )
    return rate_limiter

