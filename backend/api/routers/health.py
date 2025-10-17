"""
Health check endpoint
"""

from datetime import datetime
from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import settings
from backend.services.inference import inference_service

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        ok=True,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        models_loaded=inference_service.get_models_status()
    )

