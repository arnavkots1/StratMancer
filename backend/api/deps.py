"""
API dependencies and utilities
"""

import uuid
import logging
from typing import Optional
from fastapi import Header, HTTPException, Request
from fastapi.security import APIKeyHeader

from backend.config import settings

logger = logging.getLogger(__name__)

# API Key authentication
api_key_header = APIKeyHeader(name="X-STRATMANCER-KEY", auto_error=False)


async def verify_api_key(x_stratmancer_key: Optional[str] = Header(None)) -> str:
    """Verify API key from header"""
    if not settings.API_KEY:
        # No API key required
        return "anonymous"
    
    if not x_stratmancer_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-STRATMANCER-KEY header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_stratmancer_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_stratmancer_key


def get_correlation_id(request: Request) -> str:
    """Generate or retrieve correlation ID for request tracing"""
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict = {}  # ip -> [(timestamp, count)]
    
    async def check_rate_limit(self, request: Request):
        """Check if request exceeds rate limit"""
        if not settings.RATE_LIMIT_ENABLED:
            return
        
        import time
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if current_time - ts < 60
            ]
        
        # Check rate
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        total_requests = sum(count for _, count in self.requests[client_ip])
        
        if total_requests >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute."
            )
        
        # Add current request
        self.requests[client_ip].append((current_time, 1))


# Global rate limiter instance
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)

