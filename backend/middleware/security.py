"""
Security middleware for StratMancer API
"""

import json
import logging
import time
from typing import Dict, Any, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings

logger = logging.getLogger(__name__)

# Valid champion IDs (will be loaded from feature map)
VALID_CHAMPION_IDS: Set[int] = set()

# Required role fields
REQUIRED_ROLES = {"top", "jungle", "mid", "adc", "support"}


def load_valid_champion_ids():
    """Load valid champion IDs from feature map"""
    global VALID_CHAMPION_IDS
    try:
        import json
        with open(settings.FEATURE_MAP_PATH, 'r') as f:
            feature_map = json.load(f)
        
        # Extract champion IDs from id_to_index
        VALID_CHAMPION_IDS = set(int(champ_id) for champ_id in feature_map.get("id_to_index", {}).keys())
        logger.info(f"Loaded {len(VALID_CHAMPION_IDS)} valid champion IDs")
    except Exception as e:
        logger.error(f"Failed to load champion IDs: {e}")
        # Fallback to a reasonable range
        VALID_CHAMPION_IDS = set(range(1, 200))


def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data from logs"""
    if not settings.SANITIZE_LOGS:
        return data
    
    sanitized = data.copy()
    
    # Remove API keys
    if "api_key" in sanitized:
        sanitized["api_key"] = "***REDACTED***"
    if "X-STRATMANCER-KEY" in sanitized:
        sanitized["X-STRATMANCER-KEY"] = "***REDACTED***"
    
    # Remove sensitive headers
    sensitive_headers = ["authorization", "x-api-key", "x-stratmancer-key"]
    for header in sensitive_headers:
        if header in sanitized:
            sanitized[header] = "***REDACTED***"
    
    return sanitized


def validate_champion_id(champion_id: Any) -> bool:
    """Validate champion ID"""
    if not isinstance(champion_id, int):
        return False
    
    return champion_id in VALID_CHAMPION_IDS


def validate_draft_request(data: Dict[str, Any]) -> None:
    """Validate draft request data"""
    errors = []
    
    # Check required fields
    if "blue" not in data:
        errors.append("Missing 'blue' team data")
    if "red" not in data:
        errors.append("Missing 'red' team data")
    
    if "blue" in data and "red" in data:
        # Validate blue team
        blue_errors = validate_team_data(data["blue"], "blue")
        errors.extend(blue_errors)
        
        # Validate red team
        red_errors = validate_team_data(data["red"], "red")
        errors.extend(red_errors)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Validation failed",
                "errors": errors
            }
        )


def validate_team_data(team_data: Dict[str, Any], team_name: str) -> list:
    """Validate team data"""
    errors = []
    
    # Check required roles
    for role in REQUIRED_ROLES:
        if role not in team_data:
            errors.append(f"Missing '{role}' role in {team_name} team")
        elif team_data[role] is not None and not validate_champion_id(team_data[role]):
            errors.append(f"Invalid champion ID {team_data[role]} for {role} in {team_name} team")
    
    # Validate bans
    if "bans" in team_data:
        if not isinstance(team_data["bans"], list):
            errors.append(f"Bans must be a list in {team_name} team")
        else:
            # Deduplicate bans
            original_bans = team_data["bans"]
            team_data["bans"] = list(set(original_bans))
            
            # Validate ban champion IDs
            for i, ban_id in enumerate(team_data["bans"]):
                if not validate_champion_id(ban_id):
                    errors.append(f"Invalid ban champion ID {ban_id} at position {i} in {team_name} team")
    
    return errors


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and hardening"""
    
    def __init__(self, app):
        super().__init__(app)
        load_valid_champion_ids()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with security checks"""
        start_time = time.time()
        
        # Log request (sanitized)
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_length": request.headers.get("content-length", "0")
        }
        
        # Add API key to log (will be sanitized)
        api_key = request.headers.get("X-STRATMANCER-KEY")
        if api_key:
            log_data["X-STRATMANCER-KEY"] = api_key
        
        logger.info("Request received", extra=sanitize_log_data(log_data))
        
        try:
            # Check payload size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_PAYLOAD_SIZE:
                logger.warning(f"Oversized payload: {content_length} bytes", extra=sanitize_log_data(log_data))
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": f"Payload too large. Maximum size: {settings.MAX_PAYLOAD_SIZE} bytes"
                    }
                )
            
            # Validate specific endpoints
            if request.url.path in ["/predict-draft", "/recommend/pick", "/recommend/ban"]:
                await self._validate_prediction_request(request)
            
            # Process request with timeout
            response = await self._process_with_timeout(request, call_next)
            
            # Log response
            duration = time.time() - start_time
            logger.info("Request completed", extra={
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "path": request.url.path
            })
            
            return response
            
        except HTTPException as e:
            logger.warning(f"Request validation failed: {e.detail}", extra=sanitize_log_data(log_data))
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Unexpected error in security middleware: {e}", extra=sanitize_log_data(log_data))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    async def _validate_prediction_request(self, request: Request):
        """Validate prediction request data"""
        if request.method not in ["POST", "PUT", "PATCH"]:
            return
        
        try:
            # Read body
            body = await request.body()
            if not body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Request body is required"
                )
            
            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON: {str(e)}"
                )
            
            # Validate draft request
            validate_draft_request(data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating request: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request validation failed"
            )
    
    async def _process_with_timeout(self, request: Request, call_next):
        """Process request with timeout"""
        import asyncio
        
        try:
            # Create timeout task
            timeout_task = asyncio.create_task(
                asyncio.sleep(settings.REQUEST_TIMEOUT)
            )
            request_task = asyncio.create_task(call_next(request))
            
            # Wait for either completion or timeout
            done, pending = await asyncio.wait(
                [request_task, timeout_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check if request completed
            if request_task in done:
                return request_task.result()
            else:
                # Timeout occurred
                logger.warning(f"Request timeout after {settings.REQUEST_TIMEOUT}s", extra={
                    "path": request.url.path,
                    "method": request.method
                })
                return JSONResponse(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    content={"detail": "Request timeout"}
                )
                
        except asyncio.CancelledError:
            logger.warning("Request was cancelled", extra={
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content={"detail": "Request timeout"}
            )
