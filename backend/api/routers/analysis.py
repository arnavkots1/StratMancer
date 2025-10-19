"""
Draft analysis endpoints for post-draft insights
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

from backend.api.deps import verify_api_key
from backend.services.draft_analyzer import draft_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    dependencies=[Depends(verify_api_key)]
)


class TeamComposition(BaseModel):
    """Team composition for analysis"""
    top: int = Field(..., description="Top lane champion ID")
    jgl: int = Field(..., description="Jungle champion ID")
    mid: int = Field(..., description="Mid lane champion ID")
    adc: int = Field(..., description="ADC champion ID")
    sup: int = Field(..., description="Support champion ID")
    bans: List[int] = Field(default_factory=list, description="Banned champion IDs")


class AnalyzeDraftRequest(BaseModel):
    """Request for draft analysis"""
    blue: TeamComposition = Field(..., description="Blue team composition")
    red: TeamComposition = Field(..., description="Red team composition")
    blue_win_prob: float = Field(..., ge=0, le=1, description="Blue team win probability")
    red_win_prob: float = Field(..., ge=0, le=1, description="Red team win probability")
    elo: str = Field(..., description="ELO group (low/mid/high)")
    patch: str = Field(default="15.20", description="Game patch version")


class AnalyzeDraftResponse(BaseModel):
    """Response containing draft analysis"""
    summary: Dict[str, Any]
    blue_team: Dict[str, Any]
    red_team: Dict[str, Any]
    matchups: List[Dict[str, Any]]
    game_plan: Dict[str, List[str]]


@router.post("/draft", response_model=AnalyzeDraftResponse)
async def analyze_draft(request: AnalyzeDraftRequest):
    """
    Analyze a completed draft to provide insights on:
    - Team compositions and strengths/weaknesses
    - Lane matchups and how to play them
    - Win conditions for each team
    - Key threats to watch
    - Power spikes and game plan
    
    Requires a valid API key.
    """
    try:
        logger.info(f"Analyzing draft for {request.elo} ELO")
        
        # Convert request to dict format
        blue_team = request.blue.model_dump()
        red_team = request.red.model_dump()
        
        # Perform analysis
        analysis = draft_analyzer.analyze_draft(
            blue_team=blue_team,
            red_team=red_team,
            blue_win_prob=request.blue_win_prob,
            red_win_prob=request.red_win_prob,
            elo=request.elo,
            patch=request.patch
        )
        
        # Check for errors
        if 'error' in analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis.get('message', 'Analysis failed')
            )
        
        logger.info(f"Analysis complete: {analysis['summary']['favored_team']} favored")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Draft analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

