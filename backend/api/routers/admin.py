"""
Admin endpoints for manual job triggers and system management.
Protected by API key authentication.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Response

from backend.api.schemas import ErrorResponse
from backend.api.deps import verify_api_key, check_rate_limit
from backend.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/refresh/history-index",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Job execution failed"}
    }
)
async def trigger_history_index_refresh(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger history index refresh job.
    
    Rebuilds `/ml_pipeline/history_index.json` from all matches in `/data/processed/`.
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Standard rate limits apply
    """
    await check_rate_limit(request, response, api_key)
    
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Scheduler not initialized"
        )
    
    logger.info(f"Manual trigger: refresh_history_index (by API key: {api_key[:8]}...)")
    
    success = scheduler.run_job_now('refresh_history_index')
    
    if success:
        return {
            "status": "success",
            "job": "refresh_history_index",
            "message": "History index refresh completed successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="History index refresh failed. Check server logs for details."
        )


@router.post(
    "/refresh/model-registry",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Job execution failed"}
    }
)
async def trigger_model_registry_refresh(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger model registry refresh job.
    
    Re-reads model cards from `/ml_pipeline/models/modelcards/` to pick up newly trained models.
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Standard rate limits apply
    """
    await check_rate_limit(request, response, api_key)
    
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Scheduler not initialized"
        )
    
    logger.info(f"Manual trigger: refresh_model_registry (by API key: {api_key[:8]}...)")
    
    success = scheduler.run_job_now('refresh_model_registry')
    
    if success:
        return {
            "status": "success",
            "job": "refresh_model_registry",
            "message": "Model registry refresh completed successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Model registry refresh failed. Check server logs for details."
        )


@router.post(
    "/refresh/patch-meta",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        500: {"model": ErrorResponse, "description": "Job execution failed"}
    }
)
async def trigger_patch_meta_refresh(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Manually trigger patch metadata refresh job.
    
    Queries Riot API `/lol/status/v4/platform-data` for current patch and saves to `config/meta.json`.
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Standard rate limits apply
    """
    await check_rate_limit(request, response, api_key)
    
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Scheduler not initialized"
        )
    
    logger.info(f"Manual trigger: refresh_patch_meta (by API key: {api_key[:8]}...)")
    
    success = scheduler.run_job_now('refresh_patch_meta')
    
    if success:
        return {
            "status": "success",
            "job": "refresh_patch_meta",
            "message": "Patch metadata refresh completed successfully"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Patch metadata refresh failed. Check server logs for details."
        )


@router.get(
    "/jobs/status",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"}
    }
)
async def get_jobs_status(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get status of all background jobs.
    
    Returns information about:
    - Job schedule (next run time)
    - Execution statistics (success/error counts)
    - Last execution times
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Standard rate limits apply
    """
    await check_rate_limit(request, response, api_key)
    
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Scheduler not initialized"
        )
    
    return scheduler.get_all_jobs_status()


@router.get(
    "/jobs/{job_id}/status",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        404: {"model": ErrorResponse, "description": "Job not found"}
    }
)
async def get_job_status(
    job_id: str,
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get status of a specific background job.
    
    **Job IDs:**
    - `refresh_history_index`
    - `refresh_model_registry`
    - `refresh_patch_meta`
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Standard rate limits apply
    """
    await check_rate_limit(request, response, api_key)
    
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(
            status_code=500,
            detail="Scheduler not initialized"
        )
    
    status = scheduler.get_job_status(job_id)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )
    
    return status

