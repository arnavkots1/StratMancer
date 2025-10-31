"""
Meta tracker endpoints.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.schemas import ErrorResponse
from backend.config import settings
from backend.services.meta_tracker import meta_tracker, MetaComputationError
from backend.services.patchnote_featurizer import patchnote_featurizer
from ml_pipeline.meta_utils import normalize_patch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta", tags=["meta"])


class MetaChampion(BaseModel):
    champion_id: int = Field(..., description="Champion ID")
    champion_name: str = Field(..., description="Champion name")
    pick_rate: float = Field(..., description="Pick rate (0-1)")
    win_rate: float = Field(..., description="Win rate (0-1)")
    ban_rate: float = Field(..., description="Ban rate (0-1)")
    delta_win_rate: float = Field(..., description="Win rate delta vs previous patch")
    performance_index: float = Field(..., description="Composite performance index")
    games_played: int = Field(..., description="Number of games played")
    wins: int = Field(..., description="Number of wins")
    bans: int = Field(..., description="Number of bans")


class MetaResponse(BaseModel):
    elo: str
    patch: str
    last_updated: str
    total_matches: int
    champion_count: int
    previous_patch: Optional[str]
    available_patches: List[str]
    champions: List[MetaChampion]


class MetaTrendEntry(BaseModel):
    champion_id: int
    champion_name: str
    delta_win_rate: float
    current_win_rate: float
    previous_win_rate: Optional[float]
    performance_index: float


class MetaTrendsResponse(BaseModel):
    elo: str
    latest_patch: Optional[str]
    previous_patch: Optional[str]
    generated_at: str
    risers: List[MetaTrendEntry]
    fallers: List[MetaTrendEntry]


@router.get(
    "/trends/{elo}",
    response_model=MetaTrendsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Meta data not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def get_meta_trends(elo: str):
    """
    Retrieve risers/fallers for the most recent patch transition.
    """
    try:
        logger.info(f"Fetching meta trends for elo={elo}")
        payload = await meta_tracker.get_trends(elo)
        if not payload.get("latest_patch"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No meta trends available for elo={elo}",
            )
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed retrieving meta trends: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch meta trends")


@router.get(
    "/patchnotes/{patch}",
    responses={
        200: {"description": "Patch note features retrieved"},
        404: {"model": ErrorResponse, "description": "Patch notes not found"},
        500: {"model": ErrorResponse, "description": "Failed to fetch patch notes"},
    },
)
async def get_patchnotes_features(
    patch: str,
    refresh: bool = Query(False, description="Force refresh and bypass cache")
):
    """
    Get structured patch note features for a specific patch.
    
    Uses Gemini AI to parse Riot patch notes and extract champion-specific
    buffs, nerfs, and meta tags. Falls back to heuristic parsing if Gemini
    is unavailable.
    
    Args:
        patch: Patch version (e.g., "14.21")
        refresh: If True, bypass cache and force fresh extraction
    
    Returns:
    - patch: Normalized patch version
    - champions: List of champion changes with impact scores
    - source: "gemini", "heuristic", or "none"
    - priors: Dict mapping champion_id -> impact features
    """
    try:
        patch_norm = normalize_patch(patch)
        logger.info(f"Fetching patch note features for {patch_norm} (refresh={refresh})")
        
        features = await patchnote_featurizer.get_patch_features(patch_norm, use_cache=not refresh)
        
        # Even if champions is empty, return the structure (might be fetching or parsing in progress)
        if not features:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No patch note features available for patch {patch_norm}. The patch may not exist or patch notes may not be available yet."
            )
        
        # Return features even if champions list is empty (could be processing)
        return features
        
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid patch format: {str(exc)}")
    except Exception as exc:
        logger.error(f"Failed to fetch patch notes for {patch}: {exc}", exc_info=True)
        error_detail = str(exc) if settings.DEBUG else "Failed to fetch patch note features"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get(
    "/{elo}/latest",
    response_model=MetaResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Meta data not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def get_latest_meta(elo: str):
    """
    Retrieve the latest meta snapshot for an ELO group.
    """
    try:
        logger.info(f"Fetching latest meta snapshot for elo={elo}")
        payload = await meta_tracker.get_latest_meta(elo)
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No meta snapshots available for elo={elo}",
        )
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed retrieving latest meta snapshot: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch meta data")


@router.get(
    "/{elo}/{patch}",
    response_model=MetaResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Meta data not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def get_meta_snapshot(elo: str, patch: str):
    """
    Retrieve the meta snapshot for an ELO group and patch.
    """
    try:
        logger.info(f"Fetching meta snapshot for elo={elo} patch={patch}")
        payload = await meta_tracker.get_meta(elo, normalize_patch(patch))
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta data not found for elo={elo} patch={patch}",
        )
    except Exception as exc:  # pragma: no cover - safeguard
        logger.error(f"Failed retrieving meta snapshot: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch meta data")


@router.post(
    "/refresh",
    response_model=MetaTrendsResponse,
    responses={
        200: {"description": "Meta refresh triggered"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Failed to refresh meta"},
    },
    include_in_schema=False,
)
async def trigger_meta_refresh(elo: str = Query("mid"), patch: Optional[str] = Query(None)):
    """
    Manual refresh endpoint (hidden from public docs). Useful for admin tasks.
    """
    try:
        target_patch = normalize_patch(patch) if patch else None
        meta_tracker.refresh_all(target_patch)
        return await meta_tracker.get_trends(elo)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except MetaComputationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.error(f"Meta refresh failed: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh meta")

