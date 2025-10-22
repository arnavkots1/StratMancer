"""
FastAPI main application for StratMancer
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError

from backend.config import settings
from backend.api.routers import health, predict, models, team_optimizer, admin, recommend, analysis, meta, landing

# Optional imports for production features
try:
    from backend.services.metrics import get_metrics, get_content_type, track_request_metrics, add_request_id_header, get_request_id
    METRICS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Metrics not available: {e}")
    METRICS_AVAILABLE = False

try:
    from backend.middleware.security import SecurityMiddleware
    SECURITY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Security middleware not available: {e}")
    SECURITY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the application"""
    # Startup
    logger.info("=" * 70)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 70)
    
    # Initialize rate limiter
    from backend.services.rate_limit import init_rate_limiter
    rate_limiter = init_rate_limiter(
        redis_host=settings.REDIS_HOST,
        redis_port=settings.REDIS_PORT,
        redis_db=settings.REDIS_DB,
        use_redis=settings.USE_REDIS
    )
    logger.info(f"Rate limiter initialized (backend: {'redis' if rate_limiter.using_redis else 'memory'})")
    logger.info(f"Rate limits: IP={settings.RATE_LIMIT_PER_IP}/min, "
               f"Key={settings.RATE_LIMIT_PER_KEY}/min, Global={settings.RATE_LIMIT_GLOBAL}/min")
    
    # Initialize background scheduler
    from backend.services.scheduler import init_scheduler
    scheduler = init_scheduler()
    scheduler.start()
    logger.info("Background jobs started successfully")
    
    # Initialize services (lazy loading, so just log)
    logger.info("ML services will be initialized on first use (lazy loading)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down StratMancer API")
    
    # Stop background scheduler
    from backend.services.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    **StratMancer API** - League of Legends Draft Prediction
    
    ## Features
    
    * **Draft Prediction** - Get win probabilities with calibrated ML models
    * **Model Registry** - Access model metadata and versions
    * **Team Optimizer** - Get player team construction metrics (coming soon)
    * **Health Check** - Monitor API status
    
    ## Authentication
    
    Most endpoints require an API key in the `X-STRATMANCER-KEY` header.
    
    ## Rate Limiting
    
    - 60 requests per minute per IP address
    - Predictions are cached for 60 seconds
    
    ## Models
    
    Three ELO-specialized models:
    - **low**: IRON, BRONZE, SILVER
    - **mid**: GOLD, PLATINUM, EMERALD
    - **high**: DIAMOND, MASTER, GRANDMASTER, CHALLENGER
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Security middleware (must be first) - optional
if SECURITY_AVAILABLE:
    app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    # Generate correlation ID for tracking
    import uuid
    correlation_id = str(uuid.uuid4())
    
    # Log error with correlation ID
    logger.error(f"Unexpected error: {exc}", exc_info=True, extra={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "correlation_id": correlation_id,
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(models.router)
app.include_router(team_optimizer.router)
app.include_router(recommend.router)
app.include_router(analysis.router)
app.include_router(admin.router)
app.include_router(meta.router)
app.include_router(landing.router)

# Metrics endpoint - optional
if METRICS_AVAILABLE:
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=get_metrics(),
            media_type=get_content_type()
        )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        """Add request ID to all responses"""
        request_id = get_request_id(request)
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        add_request_id_header(response, request_id)
        
        return response


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Welcome to StratMancer API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/healthz"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
