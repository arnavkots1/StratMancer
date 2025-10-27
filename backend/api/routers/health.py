"""
Health check endpoint - absolute minimal for Railway
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
@router.get("/healthz")
async def health_check():
    """Health check endpoint - returns simple JSON"""
    return {"status": "ok"}

