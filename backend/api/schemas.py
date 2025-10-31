"""
Pydantic schemas for API requests and responses
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Schemas
# ============================================================================

class TeamDraft(BaseModel):
    """Draft for one team (blue or red)"""
    top: int = Field(..., description="Champion ID for top lane")
    jgl: int = Field(..., description="Champion ID for jungle")
    mid: int = Field(..., description="Champion ID for mid lane")
    adc: int = Field(..., description="Champion ID for ADC")
    sup: int = Field(..., description="Champion ID for support")
    bans: List[int] = Field(..., description="List of banned champion IDs (up to 5)")
    
    @field_validator('bans')
    @classmethod
    def validate_bans(cls, v):
        if len(v) > 5:
            raise ValueError('Maximum 5 bans allowed')
        return v


class PredictDraftRequest(BaseModel):
    """Request for draft prediction"""
    elo: Literal["low", "mid", "high"] = Field(..., description="ELO group")
    patch: str = Field(..., description="Game patch version (e.g., '15.20')")
    blue: TeamDraft = Field(..., description="Blue team draft")
    red: TeamDraft = Field(..., description="Red team draft")
    
    class Config:
        json_schema_extra = {
            "example": {
                "elo": "mid",
                "patch": "15.20",
                "blue": {
                    "top": 266,
                    "jgl": 64,
                    "mid": 103,
                    "adc": 51,
                    "sup": 12,
                    "bans": [53, 89, 412]
                },
                "red": {
                    "top": 24,
                    "jgl": 76,
                    "mid": 238,
                    "adc": 498,
                    "sup": 267,
                    "bans": [421, 75, 268]
                }
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class PredictDraftResponse(BaseModel):
    """Response for draft prediction"""
    blue_win_prob: float = Field(..., description="Blue team win probability")
    red_win_prob: float = Field(..., description="Red team win probability")
    confidence: float = Field(..., description="Prediction confidence (0-100 percentage)")
    calibrated: bool = Field(..., description="Whether probabilities are calibrated")
    explanations: List[str] = Field(..., description="Human-readable feature explanations")
    model_version: str = Field(..., description="Model version used")
    elo_group: str = Field(..., description="ELO group used")
    patch: str = Field(..., description="Patch version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "blue_win_prob": 0.61,
                "red_win_prob": 0.39,
                "confidence": 0.82,
                "calibrated": True,
                "explanations": [
                    "+Frontline/Engage advantage",
                    "-Low AP ratio",
                    "+Early power spike"
                ],
                "model_version": "mid-xgb-20251017",
                "elo_group": "mid",
                "patch": "15.20"
            }
        }


class ModelCard(BaseModel):
    """Model metadata"""
    elo: str
    model_type: str
    timestamp: str
    features: int
    train_size: int
    val_size: int
    test_size: int
    calibrated: bool
    source_patch: str
    feature_version: str
    model_file: str
    calibrator_file: str


class ModelsRegistryResponse(BaseModel):
    """Response for models registry"""
    models: Dict[str, ModelCard]
    feature_map_version: str
    total_champions: int
    last_updated: str


class TeamOptimizerMetrics(BaseModel):
    """Team construction metrics for a player"""
    puuid: str
    elo: str
    pick_equity: float = Field(..., description="Value of champion picks")
    economy_eff: float = Field(..., description="Resource efficiency")
    adaptability: float = Field(..., description="Meta adaptation")
    momentum: float = Field(..., description="Win streak momentum")
    macro_stability: float = Field(..., description="Macro play consistency")
    cohesion: float = Field(..., description="Team synergy")
    comfort: float = Field(..., description="Champion comfort level")
    tvs: float = Field(..., description="Team Value Score (aggregate)")


class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool
    timestamp: str
    version: str
    models_loaded: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    correlation_id: Optional[str] = None
    error_code: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Model not found for ELO group: invalid",
                "correlation_id": "abc123",
                "error_code": "MODEL_NOT_FOUND"
            }
        }

