"""
Draft prediction endpoint
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Response

from backend.api.schemas import PredictDraftRequest, PredictDraftResponse, ErrorResponse
from backend.api.deps import verify_api_key, get_correlation_id, check_rate_limit
from backend.services.inference import inference_service
from backend.services.cache import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict-draft", tags=["prediction"])


@router.post(
    "",
    response_model=PredictDraftResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def predict_draft(
    request_data: PredictDraftRequest,
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Predict draft win probability with calibrated probabilities.
    
    Takes a complete draft (blue and red teams with picks and bans) and returns:
    - Win probabilities for both teams (calibrated)
    - Confidence score
    - Human-readable explanations
    - Model version used
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:**
    - Per-IP: 60 requests/minute
    - Per-API-Key: 600 requests/minute
    - Global: 3000 requests/minute
    
    **Cached:** Identical requests are cached for 60 seconds
    """
    correlation_id = get_correlation_id(request)
    
    # Rate limiting (with API key for per-key limits)
    await check_rate_limit(request, response, api_key)
    
    try:
        # Check cache first
        cached_response = await cache_service.get_prediction(request_data.dict())
        if cached_response:
            logger.info(f"[{correlation_id}] Cache hit for prediction")
            return PredictDraftResponse(**cached_response)
        
        # Validate ELO
        if request_data.elo not in ["low", "mid", "high"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ELO group: {request_data.elo}. Must be 'low', 'mid', or 'high'."
            )
        
        # Extract team compositions
        blue_picks = [
            request_data.blue.top,
            request_data.blue.jgl,
            request_data.blue.mid,
            request_data.blue.adc,
            request_data.blue.sup
        ]
        
        red_picks = [
            request_data.red.top,
            request_data.red.jgl,
            request_data.red.mid,
            request_data.red.adc,
            request_data.red.sup
        ]
        
        # Make prediction
        logger.info(f"[{correlation_id}] Making prediction for {request_data.elo} ELO, patch {request_data.patch}")
        
        result = inference_service.predict_draft(
            elo=request_data.elo,
            patch=request_data.patch,
            blue_picks=blue_picks,
            red_picks=red_picks,
            blue_bans=request_data.blue.bans,
            red_bans=request_data.red.bans
        )
        
        # Cache the result
        await cache_service.set_prediction(request_data.dict(), result)
        
        logger.info(f"[{correlation_id}] Prediction complete: Blue {result['blue_win_prob']:.2%}, Confidence {result['confidence']:.2%}")
        
        return PredictDraftResponse(**result)
    
    except ValueError as e:
        # Model not found or feature assembly error
        logger.error(f"[{correlation_id}] ValueError: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected error
        logger.error(f"[{correlation_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail="An unexpected error occurred during prediction",
                correlation_id=correlation_id,
                error_code="PREDICTION_ERROR"
            ).dict()
        )

