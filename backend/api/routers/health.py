"""
Health check endpoint - fast startup with background model loading
"""
import threading
from datetime import datetime
from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import settings

router = APIRouter(tags=["health"])

# Global model loading state
_model_loading = False
_model_loaded = False

def _load_models_background():
    """Load ML models in background thread"""
    global _model_loading, _model_loaded
    try:
        from backend.services.inference import inference_service
        # This will trigger model loading
        inference_service.get_models_status()
        _model_loaded = True
    except Exception as e:
        print(f"Background model loading failed: {e}")
    finally:
        _model_loading = False

# Start background model loading
if not _model_loading and not _model_loaded:
    _model_loading = True
    threading.Thread(target=_load_models_background, daemon=True).start()

@router.get("/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - returns immediately"""
    return HealthResponse(
        ok=True,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        models_loaded={"status": "loading" if _model_loading else ("ready" if _model_loaded else "pending")}
    )

@router.get("/ready")
async def ready_check():
    """Ready check - returns when models are loaded"""
    return {"ready": _model_loaded, "loading": _model_loading}

