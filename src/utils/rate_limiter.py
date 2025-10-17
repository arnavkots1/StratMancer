"""
Rate limiting for Riot API requests with exponential backoff.
"""
import time
import logging
from collections import deque
from typing import Optional
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    Handles both per-second and per-2-minute limits.
    """
    
    def __init__(self, requests_per_second: int = 20, requests_per_2_minutes: int = 100):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            requests_per_2_minutes: Maximum requests per 2 minutes
        """
        self.requests_per_second = requests_per_second
        self.requests_per_2_minutes = requests_per_2_minutes
        
        # Track recent requests
        self.recent_requests = deque()  # Timestamps of requests
        self.second_window = 1.0
        self.two_minute_window = 120.0
        
        logger.info(
            f"Rate limiter initialized: {requests_per_second}/sec, "
            f"{requests_per_2_minutes}/2min"
        )
    
    def _clean_old_requests(self):
        """Remove timestamps older than 2 minutes"""
        current_time = time.time()
        cutoff_time = current_time - self.two_minute_window
        
        while self.recent_requests and self.recent_requests[0] < cutoff_time:
            self.recent_requests.popleft()
    
    def _get_requests_in_window(self, window_seconds: float) -> int:
        """Count requests in the specified time window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        return sum(1 for ts in self.recent_requests if ts >= cutoff_time)
    
    def acquire(self):
        """
        Acquire permission to make a request.
        Blocks until rate limit allows the request.
        """
        while True:
            self._clean_old_requests()
            current_time = time.time()
            
            # Check 2-minute limit
            requests_in_2min = len(self.recent_requests)
            if requests_in_2min >= self.requests_per_2_minutes:
                oldest_request = self.recent_requests[0]
                wait_time = self.two_minute_window - (current_time - oldest_request)
                if wait_time > 0:
                    logger.warning(
                        f"2-minute rate limit reached. Waiting {wait_time:.1f}s"
                    )
                    time.sleep(wait_time + 0.1)
                    continue
            
            # Check per-second limit
            requests_in_second = self._get_requests_in_window(self.second_window)
            if requests_in_second >= self.requests_per_second:
                # Wait until next second
                time.sleep(0.1)
                continue
            
            # Rate limit allows request
            self.recent_requests.append(current_time)
            return
    
    def get_status(self) -> dict:
        """Get current rate limiter status"""
        self._clean_old_requests()
        return {
            'requests_last_second': self._get_requests_in_window(1.0),
            'requests_last_2min': len(self.recent_requests),
            'limit_per_second': self.requests_per_second,
            'limit_per_2min': self.requests_per_2_minutes
        }


def handle_rate_limit_response(response: requests.Response) -> Optional[int]:
    """
    Check response headers for rate limit information.
    
    Args:
        response: HTTP response object
        
    Returns:
        Seconds to wait if rate limited, None otherwise
    """
    if response.status_code == 429:
        # Rate limit exceeded
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            wait_seconds = int(retry_after)
            logger.warning(f"Rate limit hit. Retry-After: {wait_seconds}s")
            return wait_seconds
        return 60  # Default wait time
    
    return None


def retry_on_rate_limit(func):
    """
    Decorator to retry API calls with exponential backoff on rate limit errors.
    """
    @retry(
        retry=retry_if_exception_type((RateLimitExceeded, requests.exceptions.RequestException)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            
            # Check for rate limit in response
            if isinstance(response, requests.Response):
                wait_time = handle_rate_limit_response(response)
                if wait_time:
                    time.sleep(wait_time)
                    raise RateLimitExceeded("Rate limit exceeded, retrying...")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    return wrapper

