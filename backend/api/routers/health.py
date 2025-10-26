"""
Health check endpoint
"""

from datetime import datetime
from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - fast startup without loading models"""
    return HealthResponse(
        ok=True,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        models_loaded={"status": "ready", "note": "Models will load on first prediction request"}
    )

