"""
FastAPI main application for StratMancer
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.config import settings
from backend.api.routers import health, predict, models, team_optimizer, admin

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
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
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(models.router)
app.include_router(team_optimizer.router)
app.include_router(admin.router)


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

