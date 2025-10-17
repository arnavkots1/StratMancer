"""
API dependencies and utilities
"""

import uuid
import logging
from typing import Optional
from fastapi import Header, HTTPException, Request, Response
from fastapi.security import APIKeyHeader

from backend.config import settings
from backend.services.rate_limit import get_rate_limiter

logger = logging.getLogger(__name__)

# API Key authentication
api_key_header = APIKeyHeader(name="X-STRATMANCER-KEY", auto_error=False)


async def verify_api_key(x_stratmancer_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from header.
    Required for POST /predict-draft and /team-optimizer routes.
    """
    if not settings.API_KEY:
        # No API key required in this environment
        return "anonymous"
    
    if not x_stratmancer_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-STRATMANCER-KEY header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_stratmancer_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_stratmancer_key


async def check_rate_limit(request: Request, response: Response, api_key: Optional[str] = None):
    """
    Check rate limits using token bucket algorithm.
    
    Three tiers:
    - Per-IP: 60 req/min
    - Per-API-Key: 600 req/min
    - Global: 3000 req/min
    
    Args:
        request: FastAPI request object
        response: FastAPI response object (for setting Retry-After header)
        api_key: API key from authentication (optional)
    
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    limiter = get_rate_limiter()
    client_ip = request.client.host
    
    # Check rate limits
    allowed, limit_type, retry_after = limiter.check_rate_limit(client_ip, api_key)
    
    if not allowed:
        # Set Retry-After header
        retry_after_int = int(retry_after) + 1  # Round up
        response.headers["Retry-After"] = str(retry_after_int)
        
        # Get limit info for error message
        limit_info = limiter.get_limit_info(limit_type)
        
        error_messages = {
            'per_ip': f"IP rate limit exceeded. Max {limit_info['refill_rate_per_minute']:.0f} requests per minute per IP.",
            'per_key': f"API key rate limit exceeded. Max {limit_info['refill_rate_per_minute']:.0f} requests per minute per key.",
            'global': f"Global rate limit exceeded. Max {limit_info['refill_rate_per_minute']:.0f} requests per minute."
        }
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": error_messages.get(limit_type, "Rate limit exceeded"),
                "limit_type": limit_type,
                "retry_after": retry_after_int,
                "backend": limit_info['backend']
            },
            headers={"Retry-After": str(retry_after_int)}
        )


def get_correlation_id(request: Request) -> str:
    """Generate or retrieve correlation ID for request tracing"""
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    return correlation_id

