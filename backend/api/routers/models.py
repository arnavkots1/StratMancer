"""
Model registry endpoints
"""

from fastapi import APIRouter, HTTPException

from backend.api.schemas import ModelsRegistryResponse, ModelCard
from backend.services.model_registry import model_registry

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/registry", response_model=ModelsRegistryResponse)
async def get_models_registry():
    """
    Get current model registry with ELO-specific model cards.
    
    Returns metadata for all available models including:
    - Model type and version
    - Training metrics
    - Feature version
    - Source patch
    """
    try:
        # Ensure registry is loaded
        model_registry.load_registry()
        
        # Get all modelcards
        modelcards = model_registry.get_all_modelcards()
        
        # Convert to response format
        models_dict = {
            elo: ModelCard(**card)
            for elo, card in modelcards.items()
        }
        
        return ModelsRegistryResponse(
            models=models_dict,
            feature_map_version=model_registry.get_feature_map_version(),
            total_champions=model_registry.get_total_champions(),
            last_updated=model_registry.get_last_updated()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model registry: {str(e)}"
        )


@router.post("/registry/reload")
async def reload_registry():
    """
    Force reload of model registry.
    Useful after training new models.
    """
    try:
        model_registry.reload()
        return {"message": "Model registry reloaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload registry: {str(e)}"
        )

