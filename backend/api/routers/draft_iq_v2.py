"""
Draft IQ v2 endpoint - Professional coach-style draft analysis
"""

import logging
import hashlib
import json
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict

from backend.api.schemas import PredictDraftRequest
from backend.api.deps import verify_api_key, get_correlation_id, check_rate_limit
from backend.services.draft_iq_v2 import get_draft_iq_v2_service, to_markdown, DraftIQV2
from backend.services.cache import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/draft-iq/v2", tags=["draft-iq"])


@router.post("/explain")
async def explain_v2(
    request_data: PredictDraftRequest,
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate Draft IQ v2 analysis with structured JSON and Markdown.
    
    Returns professional coach-style analysis including:
    - Team overview tables with role/champion/notes
    - Team identity paragraphs
    - Lane-by-lane analysis
    - Teamfighting/Scaling/Execution comparison
    - Phase predictions (Early/Mid/Late)
    - Final calibrated win probabilities with ranges
    
    **Authentication Required:** X-STRATMANCER-KEY header
    
    **Rate Limited:** Same bucket as /predict-draft
    
    **Cached:** Results cached for 60 seconds by draft state hash
    """
    correlation_id = get_correlation_id(request)
    
    # Rate limiting (same as predict-draft) - skip if not initialized
    try:
        await check_rate_limit(request, None, api_key)
    except RuntimeError as e:
        if "Rate limiter not initialized" in str(e):
            logger.warning(f"[{correlation_id}] Rate limiter not initialized, skipping rate limit check")
        else:
            raise
    
    try:
        # Build cache key
        cache_key_data = {
            "elo": request_data.elo,
            "patch": request_data.patch,
            "blue": request_data.blue.model_dump(),
            "red": request_data.red.model_dump()
        }
        cache_key_str = json.dumps(cache_key_data, sort_keys=True)
        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
        cache_key = f"draft_iq_v2:{cache_key_hash}"
        
        # Check cache
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"[{correlation_id}] Cache hit for Draft IQ v2")
            cached_data = json.loads(cached)
            # Reconstruct DraftIQV2 from cached dict for markdown conversion
            try:
                iq_cached = DraftIQV2(**cached_data)
                markdown_output = to_markdown(iq_cached)
            except Exception as e:
                logger.warning(f"Failed to convert cached data to markdown: {e}")
                # Generate markdown from dict directly
                markdown_output = f"# Draft IQ v2 Analysis\n\nCached result (JSON only)\n"
            return {
                "json": cached_data,
                "markdown": markdown_output
            }
        
        # Validate ELO
        if request_data.elo not in ["low", "mid", "high"]:
            raise HTTPException(status_code=400, detail="Invalid ELO group. Must be 'low', 'mid', or 'high'")
        
        # Convert draft to positional arrays
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
        
        # Generate analysis
        service = get_draft_iq_v2_service()
        iq_result = await service.explain_draft_v2(
            elo=request_data.elo,
            patch=request_data.patch,
            blue_picks=blue_picks,
            red_picks=red_picks,
            blue_bans=request_data.blue.bans,
            red_bans=request_data.red.bans
        )
        
        # Convert to dict for JSON response
        iq_dict = iq_result.model_dump()
        
        # Generate markdown
        markdown_output = to_markdown(iq_result)
        
        # Cache result (60 seconds)
        cache_value = json.dumps(iq_dict)
        await cache_service.set(cache_key, cache_value, ttl=60)
        
        logger.info(f"[{correlation_id}] Draft IQ v2 analysis generated")
        
        return {
            "json": iq_dict,
            "markdown": markdown_output
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{correlation_id}] Draft IQ v2 failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Draft IQ v2 analysis failed: {str(e)}"
        )

