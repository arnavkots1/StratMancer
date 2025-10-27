"""
Simplified FastAPI app for Railway deployment - WORKING VERSION
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="StratMancer API - League of Legends Draft Prediction"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Simple health endpoint
@app.get("/health")
@app.get("/healthz")
async def health_check():
    """Simple health check"""
    return {
        "ok": True,
        "status": "healthy",
        "version": settings.APP_VERSION
    }

# Add ML routers - import them safely
try:
    from backend.api.routers import predict
    app.include_router(predict.router)
    logger.info("Predict router loaded")
except Exception as e:
    logger.error(f"Failed to load predict router: {e}")

try:
    from backend.api.routers import models
    app.include_router(models.router)
    logger.info("Models router loaded")
except Exception as e:
    logger.error(f"Failed to load models router: {e}")

try:
    from backend.api.routers import landing
    app.include_router(landing.router)
    logger.info("Landing router loaded")
except Exception as e:
    logger.error(f"Failed to load landing router: {e}")

try:
    from backend.api.routers import meta
    app.include_router(meta.router)
    logger.info("Meta router loaded")
except Exception as e:
    logger.error(f"Failed to load meta router: {e}")

try:
    from backend.api.routers import recommend
    app.include_router(recommend.router)
    logger.info("Recommend router loaded")
except Exception as e:
    logger.error(f"Failed to load recommend router: {e}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StratMancer API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": ["/predict-draft", "/predict-meta", "/recommend", "/models"]
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
