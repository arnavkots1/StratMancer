"""
Champion recommendation endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

from backend.api.deps import verify_api_key, get_correlation_id, check_rate_limit
from backend.services.recommender import recommender_service
from backend.api.schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommendations"])


class TeamDraftState(BaseModel):
    """Draft state for one team"""
    top: Optional[int] = Field(None, description="Champion ID for top (if picked)")
    jgl: Optional[int] = Field(None, description="Champion ID for jungle (if picked)")
    mid: Optional[int] = Field(None, description="Champion ID for mid (if picked)")
    adc: Optional[int] = Field(None, description="Champion ID for ADC (if picked)")
    sup: Optional[int] = Field(None, description="Champion ID for support (if picked)")
    bans: List[int] = Field(default_factory=list, description="List of banned champion IDs")


class RecommendPickRequest(BaseModel):
    """Request for pick recommendations"""
    elo: Literal["low", "mid", "high"] = Field(..., description="ELO group")
    side: Literal["blue", "red"] = Field(..., description="Team side")
    role: Literal["top", "jgl", "mid", "adc", "sup"] = Field(..., description="Role to fill")
    blue: TeamDraftState = Field(..., description="Blue team draft state")
    red: TeamDraftState = Field(..., description="Red team draft state")
    patch: str = Field("15.20", description="Patch version")
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "elo": "mid",
                "side": "blue",
                "role": "jgl",
                "blue": {
                    "top": 266,
                    "jgl": None,
                    "mid": None,
                    "adc": None,
                    "sup": None,
                    "bans": [53, 89]
                },
                "red": {
                    "top": 24,
                    "jgl": None,
                    "mid": None,
                    "adc": None,
                    "sup": None,
                    "bans": [421, 75]
                },
                "patch": "15.20",
                "top_n": 5
            }
        }


class RecommendBanRequest(BaseModel):
    """Request for ban recommendations"""
    elo: Literal["low", "mid", "high"] = Field(..., description="ELO group")
    side: Literal["blue", "red"] = Field(..., description="Team side")
    blue: TeamDraftState = Field(..., description="Blue team draft state")
    red: TeamDraftState = Field(..., description="Red team draft state")
    patch: str = Field("15.20", description="Patch version")
    top_n: int = Field(5, ge=1, le=20, description="Number of recommendations")


class ChampionRecommendation(BaseModel):
    """Single champion recommendation"""
    champion_id: int = Field(..., description="Champion ID")
    champion_name: str = Field(..., description="Champion name")
    win_gain: float = Field(..., description="Expected win rate gain")
    raw_win_gain: Optional[float] = Field(None, description="Raw win gain before ELO adjustment")
    reasons: List[str] = Field(..., description="Reasons why this pick is recommended")


class BanRecommendation(BaseModel):
    """Single ban recommendation"""
    champion_id: int = Field(..., description="Champion ID")
    champion_name: str = Field(..., description="Champion name")
    threat_level: float = Field(..., description="Threat level (win rate loss if enemy picks)")
    reasons: List[str] = Field(..., description="Reasons why this champion should be banned")


class PickRecommendationResponse(BaseModel):
    """Response for pick recommendations"""
    side: str = Field(..., description="Team side")
    role: str = Field(..., description="Role being filled")
    baseline_winrate: float = Field(..., description="Current draft win rate")
    recommendations: List[ChampionRecommendation] = Field(..., description="Top recommended picks")
    model_version: str = Field(..., description="Model version used")
    elo: str = Field(..., description="ELO group")
    evaluated_champions: int = Field(..., description="Number of champions evaluated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "side": "blue",
                "role": "jungle",
                "baseline_winrate": 0.52,
                "recommendations": [
                    {
                        "champion_id": 64,
                        "champion_name": "Lee Sin",
                        "win_gain": 0.042,
                        "raw_win_gain": 0.039,
                        "reasons": ["+Early power spike", "+High mobility", "+Strong engage"]
                    },
                    {
                        "champion_id": 11,
                        "champion_name": "Master Yi",
                        "win_gain": 0.038,
                        "raw_win_gain": 0.041,
                        "reasons": ["+Late game scaling", "+High mobility", "+Mixed damage"]
                    }
                ],
                "model_version": "mid-xgb-recommender",
                "elo": "mid",
                "evaluated_champions": 95
            }
        }


class BanRecommendationResponse(BaseModel):
    """Response for ban recommendations"""
    side: str = Field(..., description="Team side")
    recommendations: List[BanRecommendation] = Field(..., description="Top recommended bans")
    model_version: str = Field(..., description="Model version used")
    elo: str = Field(..., description="ELO group")
    evaluated_champions: int = Field(..., description="Number of champions evaluated")


@router.post(
    "/pick",
    response_model=PickRecommendationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def recommend_pick(
    request_data: RecommendPickRequest,
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Get champion pick recommendations for current draft state.
    
    Analyzes the current draft and suggests the best champions to pick next
    for the specified role. Each recommendation includes:
    - Expected win rate improvement
    - Human-readable explanations
    - ELO-adjusted ratings
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:**
    - Per-IP: 60 requests/minute
    - Per-API-Key: 600 requests/minute
    """
    correlation_id = get_correlation_id(request)
    
    # Rate limiting
    await check_rate_limit(request, response, api_key)
    
    try:
        logger.info(f"[{correlation_id}] Pick recommendation: {request_data.elo} {request_data.side} {request_data.role}")
        
        # Convert request to draft dict
        draft = {
            'blue': {
                'top': request_data.blue.top,
                'jgl': request_data.blue.jgl,
                'mid': request_data.blue.mid,
                'adc': request_data.blue.adc,
                'sup': request_data.blue.sup,
                'bans': request_data.blue.bans
            },
            'red': {
                'top': request_data.red.top,
                'jgl': request_data.red.jgl,
                'mid': request_data.red.mid,
                'adc': request_data.red.adc,
                'sup': request_data.red.sup,
                'bans': request_data.red.bans
            }
        }
        
        # Get recommendations
        result = recommender_service.recommend_next_pick(
            elo=request_data.elo,
            side=request_data.side,
            draft=draft,
            role=request_data.role,
            patch=request_data.patch,
            top_n=request_data.top_n
        )
        
        logger.info(f"[{correlation_id}] Recommendations generated: {len(result.get('recommendations', []))} options")
        
        return PickRecommendationResponse(**result)
    
    except ValueError as e:
        logger.error(f"[{correlation_id}] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/ban",
    response_model=BanRecommendationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def recommend_ban(
    request_data: RecommendBanRequest,
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Get champion ban recommendations for current draft state.
    
    Analyzes which enemy champions would hurt your team the most
    if picked. Each recommendation includes:
    - Threat level (win rate loss)
    - Reasons why this champion is dangerous
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:**
    - Per-IP: 60 requests/minute
    - Per-API-Key: 600 requests/minute
    """
    correlation_id = get_correlation_id(request)
    
    # Rate limiting
    await check_rate_limit(request, response, api_key)
    
    try:
        logger.info(f"[{correlation_id}] Ban recommendation: {request_data.elo} {request_data.side}")
        
        # Convert request to draft dict
        draft = {
            'blue': {
                'top': request_data.blue.top,
                'jgl': request_data.blue.jgl,
                'mid': request_data.blue.mid,
                'adc': request_data.blue.adc,
                'sup': request_data.blue.sup,
                'bans': request_data.blue.bans
            },
            'red': {
                'top': request_data.red.top,
                'jgl': request_data.red.jgl,
                'mid': request_data.red.mid,
                'adc': request_data.red.adc,
                'sup': request_data.red.sup,
                'bans': request_data.red.bans
            }
        }
        
        # Get recommendations
        result = recommender_service.recommend_bans(
            elo=request_data.elo,
            side=request_data.side,
            draft=draft,
            patch=request_data.patch,
            top_n=request_data.top_n
        )
        
        logger.info(f"[{correlation_id}] Ban recommendations generated: {len(result.get('recommendations', []))} options")
        
        return BanRecommendationResponse(**result)
    
    except ValueError as e:
        logger.error(f"[{correlation_id}] ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"[{correlation_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


