"""
Prometheus metrics and OpenTelemetry tracing for StratMancer
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import uuid

logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'stratmancer_requests_total',
    'Total number of HTTP requests',
    ['method', 'route', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'stratmancer_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'route'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

PREDICT_INFERENCE_MS = Histogram(
    'stratmancer_predict_inference_milliseconds',
    'Model inference time in milliseconds',
    ['elo_group', 'model_type'],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)

RECOMMENDATION_COUNT = Counter(
    'stratmancer_recommendations_total',
    'Total number of recommendations generated',
    ['type', 'elo_group']
)

ACTIVE_CONNECTIONS = Gauge(
    'stratmancer_active_connections',
    'Number of active connections'
)

MODEL_LOAD_TIME = Histogram(
    'stratmancer_model_load_seconds',
    'Time to load ML models',
    ['elo_group', 'model_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Global state for tracking
_active_connections = 0
_request_ids: Dict[str, str] = {}


def get_metrics() -> str:
    """Generate Prometheus metrics"""
    return generate_latest()


def get_content_type() -> str:
    """Get Prometheus content type"""
    return CONTENT_TYPE_LATEST


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())


def get_request_id(request: Request) -> str:
    """Get or generate request ID for tracing"""
    # Check if already in our tracking
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{request.url.path}"
    
    if key not in _request_ids:
        _request_ids[key] = generate_request_id()
    
    return _request_ids[key]


def track_request_metrics(func):
    """Decorator to track request metrics"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        start_time = time.time()
        request_id = get_request_id(request)
        
        # Track active connections
        global _active_connections
        _active_connections += 1
        ACTIVE_CONNECTIONS.set(_active_connections)
        
        # Add request ID to headers
        response = None
        status_code = 500
        
        try:
            # Call the actual function
            if asyncio.iscoroutinefunction(func):
                response = await func(request, *args, **kwargs)
            else:
                response = func(request, *args, **kwargs)
            
            # Extract status code
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            elif isinstance(response, dict) and 'status_code' in response:
                status_code = response['status_code']
            else:
                status_code = 200
                
        except Exception as e:
            logger.error(f"Request failed: {e}", extra={
                'request_id': request_id,
                'path': request.url.path,
                'method': request.method
            })
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            _active_connections -= 1
            ACTIVE_CONNECTIONS.set(_active_connections)
            
            REQUEST_COUNT.labels(
                method=request.method,
                route=request.url.path,
                status_code=status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                route=request.url.path
            ).observe(duration)
            
            # Log request completion
            logger.info(f"Request completed", extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': status_code,
                'duration_ms': round(duration * 1000, 2)
            })
        
        return response
    
    return wrapper


def track_inference_time(elo_group: str, model_type: str):
    """Decorator to track model inference time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                PREDICT_INFERENCE_MS.labels(
                    elo_group=elo_group,
                    model_type=model_type
                ).observe(duration_ms)
                
                logger.debug(f"Inference completed", extra={
                    'elo_group': elo_group,
                    'model_type': model_type,
                    'duration_ms': round(duration_ms, 2)
                })
        return wrapper
    return decorator


def track_model_load_time(elo_group: str, model_type: str):
    """Decorator to track model loading time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                MODEL_LOAD_TIME.labels(
                    elo_group=elo_group,
                    model_type=model_type
                ).observe(duration)
                
                logger.info(f"Model loaded", extra={
                    'elo_group': elo_group,
                    'model_type': model_type,
                    'duration_seconds': round(duration, 2)
                })
        return wrapper
    return decorator


def track_recommendation(recommendation_type: str, elo_group: str, count: int = 1):
    """Track recommendation generation"""
    RECOMMENDATION_COUNT.labels(
        type=recommendation_type,
        elo_group=elo_group
    ).inc(count)
    
    logger.info(f"Recommendations generated", extra={
        'type': recommendation_type,
        'elo_group': elo_group,
        'count': count
    })


def add_request_id_header(response: Response, request_id: str):
    """Add request ID to response headers"""
    response.headers["X-Request-ID"] = request_id
    return response


# Import asyncio for the decorator
import asyncio
