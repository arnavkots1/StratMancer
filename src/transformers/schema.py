"""
Match data schema definition using Pydantic for validation.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator


class ChampionStats(BaseModel):
    """Per-champion statistics"""
    id: int = Field(..., description="Champion ID")
    role: str = Field(..., description="Lane role (TOP, JUNGLE, MID, ADC, SUPPORT)")
    kda: float = Field(..., description="Kill-Death-Assist ratio")
    cs: float = Field(..., description="Creep score per minute")
    dmg_share: float = Field(..., ge=0, le=1, description="Damage share (0-1)")
    gold_share: float = Field(..., ge=0, le=1, description="Gold share (0-1)")

    @validator('kda')
    def validate_kda(cls, v):
        if v < 0:
            return 0.0
        return round(v, 2)
    
    @validator('cs')
    def validate_cs(cls, v):
        return round(v, 2) if v >= 0 else 0.0


class Objectives(BaseModel):
    """Team objectives"""
    dragons: int = Field(default=0, ge=0)
    heralds: int = Field(default=0, ge=0)
    barons: int = Field(default=0, ge=0)
    towers: int = Field(default=0, ge=0)


class DerivedFeatures(BaseModel):
    """Computed team composition features"""
    ap_ad_ratio: float = Field(..., description="AP to AD damage ratio")
    engage_score: float = Field(..., ge=0, description="Team engage potential")
    splitpush_score: float = Field(..., ge=0, description="Splitpush potential")
    teamfight_synergy: float = Field(..., ge=0, le=1, description="Teamfight synergy score")

    @validator('ap_ad_ratio', 'engage_score', 'splitpush_score', 'teamfight_synergy')
    def round_features(cls, v):
        return round(v, 3)


class MatchData(BaseModel):
    """Complete match data schema"""
    match_id: str = Field(..., description="Unique match identifier")
    patch: str = Field(..., description="Game patch version (e.g., '14.1')")
    elo_rank: str = Field(..., description="Rank tier (IRON, BRONZE, ..., CHALLENGER)")
    
    blue_picks: List[int] = Field(..., min_items=5, max_items=5, description="Blue team champion picks")
    red_picks: List[int] = Field(..., min_items=5, max_items=5, description="Red team champion picks")
    blue_bans: List[int] = Field(..., min_items=5, max_items=5, description="Blue team bans")
    red_bans: List[int] = Field(..., min_items=5, max_items=5, description="Red team bans")
    
    blue_win: bool = Field(..., description="True if blue team won")
    
    champion_stats: List[ChampionStats] = Field(..., min_items=10, max_items=10, 
                                                  description="Stats for all 10 champions")
    
    blue_objectives: Objectives = Field(..., description="Blue team objectives")
    red_objectives: Objectives = Field(..., description="Red team objectives")
    
    derived_features: DerivedFeatures = Field(..., description="Computed features")
    
    @validator('elo_rank')
    def validate_rank(cls, v):
        valid_ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 
                       'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
        v_upper = v.upper()
        if v_upper not in valid_ranks:
            raise ValueError(f"Invalid rank: {v}. Must be one of {valid_ranks}")
        return v_upper
    
    @validator('blue_picks', 'red_picks')
    def validate_picks_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate champions in picks")
        return v
    
    @validator('blue_bans', 'red_bans')
    def validate_bans(cls, v):
        # Bans can have duplicates or be 0 (no ban)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "NA1_4567890123",
                "patch": "14.1",
                "elo_rank": "GOLD",
                "blue_picks": [1, 2, 3, 4, 5],
                "red_picks": [6, 7, 8, 9, 10],
                "blue_bans": [11, 12, 13, 14, 15],
                "red_bans": [16, 17, 18, 19, 20],
                "blue_win": True,
                "champion_stats": [],
                "blue_objectives": {"dragons": 3, "heralds": 1, "barons": 1, "towers": 8},
                "red_objectives": {"dragons": 1, "heralds": 0, "barons": 0, "towers": 3},
                "derived_features": {
                    "ap_ad_ratio": 0.6,
                    "engage_score": 7.5,
                    "splitpush_score": 5.2,
                    "teamfight_synergy": 0.75
                }
            }
        }


def validate_match(match_dict: Dict) -> MatchData:
    """
    Validate a match dictionary against the schema.
    
    Args:
        match_dict: Dictionary containing match data
        
    Returns:
        Validated MatchData object
        
    Raises:
        ValidationError: If data doesn't match schema
    """
    return MatchData(**match_dict)

