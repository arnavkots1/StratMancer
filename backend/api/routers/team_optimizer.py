"""
Team optimizer endpoints
"""

from fastapi import APIRouter, HTTPException, Path, Depends, Request, Response

from backend.api.schemas import TeamOptimizerMetrics, ErrorResponse
from backend.api.deps import verify_api_key, check_rate_limit
from backend.services.team_optimizer import team_optimizer_service

router = APIRouter(prefix="/team-optimizer", tags=["team-optimizer"])


@router.get(
    "/player/{puuid}",
    response_model=TeamOptimizerMetrics,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Player not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
async def get_player_metrics(
    puuid: str = Path(..., description="Player PUUID", min_length=10),
    request: Request = None,
    response: Response = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get team construction metrics for a player.
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:**
    - Per-IP: 60 requests/minute
    - Per-API-Key: 600 requests/minute
    - Global: 3000 requests/minute
    
    Returns various metrics for team building:
    - **pick_equity**: Value of champion picks
    - **economy_eff**: Resource efficiency
    - **adaptability**: Meta adaptation capability
    - **momentum**: Win streak momentum
    - **macro_stability**: Macro play consistency
    - **cohesion**: Team synergy
    - **comfort**: Champion comfort level
    - **tvs**: Team Value Score (aggregate metric)
    
    **Note:** This feature requires precomputed player data.
    If no data is available, a 404 error is returned.
    """
    # Rate limiting
    await check_rate_limit(request, response, api_key)
    
    # Get player metrics
    metrics = team_optimizer_service.get_player_metrics(puuid)
    
    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                detail=f"No team metrics found for player: {puuid}",
                error_code="PLAYER_NOT_FOUND"
            ).dict()
        )
    
    return TeamOptimizerMetrics(**metrics)

