"""
Health check endpoint
"""

from datetime import datetime
from fastapi import APIRouter
import os

from backend.api.schemas import HealthResponse
from backend.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - simplified for production"""
    try:
        # Simple health check without ML dependencies
        return HealthResponse(
            ok=True,
            timestamp=datetime.now().isoformat(),
            version=settings.APP_VERSION,
            models_loaded={"status": "simplified", "note": "ML models not loaded in production"}
        )
    except Exception as e:
        # Fallback health check
        return HealthResponse(
            ok=True,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            models_loaded={"status": "fallback", "error": str(e)}
        )

