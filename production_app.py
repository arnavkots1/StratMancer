"""
Production-ready FastAPI app with lazy loading
"""
import logging
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StratMancer API",
    version="1.0.0",
    description="League of Legends Draft Prediction API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global variables for lazy loading
_inference_service = None
_settings = None

def get_settings():
    """Lazy load settings"""
    global _settings
    if _settings is None:
        try:
            from backend.config import settings
            _settings = settings
            logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Fallback settings
            _settings = type('Settings', (), {
                'APP_NAME': 'StratMancer API',
                'APP_VERSION': '1.0.0',
                'API_KEY': os.getenv('API_KEY', 'dev-key')
            })()
    return _settings

def get_inference_service():
    """Lazy load inference service"""
    global _inference_service
    if _inference_service is None:
        try:
            from backend.services.inference import inference_service
            _inference_service = inference_service
            logger.info("Inference service loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load inference service: {e}")
            _inference_service = None
    return _inference_service

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    settings = get_settings()
    return {
        "message": "Welcome to StratMancer API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

# Health endpoint - FAST startup
@app.get("/health")
@app.get("/healthz")
async def health():
    """Health check - no ML dependencies"""
    settings = get_settings()
    return {
        "ok": True,
        "status": "healthy",
        "version": settings.APP_VERSION,
        "models_loaded": "lazy"
    }

# Prediction endpoint - lazy loads ML models
@app.post("/predict-draft")
async def predict_draft(request: Request):
    """Draft prediction endpoint"""
    try:
        # Get request data
        data = await request.json()
        
        # Lazy load inference service
        inference_service = get_inference_service()
        if inference_service is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "ML service not available"}
            )
        
        # Make prediction
        result = inference_service.predict_draft(
            elo=data.get('elo', 'mid'),
            blue_team=data.get('blue_team', []),
            red_team=data.get('red_team', []),
            context=data.get('context', {})
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Prediction failed"}
        )

# Models endpoint - lazy loads model info
@app.get("/models/registry")
async def get_models():
    """Get model registry"""
    try:
        inference_service = get_inference_service()
        if inference_service is None:
            return {"models": [], "status": "not_loaded"}
        
        return inference_service.get_models_status()
        
    except Exception as e:
        logger.error(f"Models error: {e}")
        return {"models": [], "status": "error", "message": str(e)}

# Landing endpoint - simple data
@app.get("/landing/")
async def get_landing_data():
    """Landing page data"""
    return {
        "modelConfidence": 32,
        "totalMatches": 1000,
        "lastUpdated": "2025-01-01",
        "status": "active"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
