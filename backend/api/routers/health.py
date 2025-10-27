"""
Health check endpoint - minimal for Railway
"""
from datetime import datetime
from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import settings

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - minimal, no ML imports"""
    return HealthResponse(
        ok=True,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        models_loaded={"status": "lazy", "note": "Models load on first prediction"}
    )

