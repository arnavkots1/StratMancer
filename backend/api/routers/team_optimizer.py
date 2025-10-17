"""
Team optimizer endpoints
"""

from fastapi import APIRouter, HTTPException, Path

from backend.api.schemas import TeamOptimizerMetrics, ErrorResponse
from backend.services.team_optimizer import team_optimizer_service

router = APIRouter(prefix="/team-optimizer", tags=["team-optimizer"])


@router.get(
    "/player/{puuid}",
    response_model=TeamOptimizerMetrics,
    responses={
        404: {"model": ErrorResponse, "description": "Player not found"}
    }
)
async def get_player_metrics(
    puuid: str = Path(..., description="Player PUUID", min_length=10)
):
    """
    Get team construction metrics for a player.
    
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

