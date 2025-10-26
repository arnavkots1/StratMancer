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
    """Health check endpoint"""
    try:
        # Try to get ML models status
        from backend.services.inference import inference_service
        models_status = inference_service.get_models_status()
    except Exception as e:
        # Fallback if ML services aren't available
        models_status = {"status": "error", "message": str(e)}
    
    return HealthResponse(
        ok=True,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        models_loaded=models_status
    )

