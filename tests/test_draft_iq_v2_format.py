"""
Tests for Draft IQ v2 format validation (fallback builder)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.draft_iq_v2 import DraftIQV2Service


def test_fallback_builder_format():
    """Test that fallback builder produces valid format"""
    service = DraftIQV2Service()
    
    # Mock prediction result
    prediction_result = {
        "blue_win_prob": 0.45,
        "blue_win_prob_calibrated": 0.42,
        "confidence": 16.0,
        "model_version": "mid-xgb-20251101"
    }
    
    named_features = {
        "comp_features": {
            "blue_ap_ad_ratio": 0.4,
            "red_ap_ad_ratio": 0.6,
            "blue_engage_score": 0.7,
            "red_engage_score": 0.5,
            "engage_diff": 0.2,
            "early_diff": -0.1,
            "mid_diff": 0.0,
            "late_diff": 0.15
        }
    }
    
    # Build fallback analysis
    result = service._build_fallback_analysis(
        elo="mid",
        patch="15.20",
        blue_picks=[266, 64, 103, 51, 12],
        red_picks=[24, 76, 238, 498, 267],
        blue_bans=[],
        red_bans=[],
        prediction_result=prediction_result,
        named_features=named_features
    )
    
    # Validate structure
    assert result.elo_context in ["High", "Mid", "Low"]
    assert result.patch == "15.20"
    assert len(result.blue_overview.items) > 0
    assert len(result.red_overview.items) > 0
    assert len(result.blue_overview.items) <= 5
    assert len(result.red_overview.items) <= 5
    assert len(result.lane_by_lane) == 4  # Top, Jungle, Mid, Bot
    assert len(result.teamfight_scaling_execution) >= 3
    assert len(result.phase_predictions) == 3
    
    # Validate team overview items
    for item in result.blue_overview.items:
        assert item.role in ["Top", "Jungle", "Mid", "ADC", "Support"]
        assert len(item.champion) > 0
        assert len(item.notes) > 0
    
    # Validate lane outcomes
    lanes = {lane.lane for lane in result.lane_by_lane}
    assert lanes == {"Top", "Jungle", "Mid", "Bot"}
    
    for lane in result.lane_by_lane:
        assert lane.likely_winner in [
            "Blue early", "Blue", "Even", "Red", "Red later",
            "Slight Blue early, Red later",
            "Skill-based, slightly Blue",
            "Skill-based, slightly Red"
        ]
        assert len(lane.explanation) > 0
    
    # Validate phase predictions
    phases = {phase.phase for phase in result.phase_predictions}
    assert phases == {"Early (0-10 min)", "Mid (10-25 min)", "Late (25+ min)"}
    
    for phase in result.phase_predictions:
        assert phase.favored in [
            "Blue", "Red", "Even", "Slight Blue", "Slight Red",
            "Red >> Blue", "Blue >> Red"
        ]
        assert len(phase.comment) > 0
    
    # Validate probability ranges format
    assert " – " in result.final_prediction.blue_range
    assert "%" in result.final_prediction.blue_range
    assert " – " in result.final_prediction.red_range
    assert "%" in result.final_prediction.red_range
    
    # Parse ranges to ensure they're valid numbers
    blue_range_parts = result.final_prediction.blue_range.replace(" %", "").split(" – ")
    assert len(blue_range_parts) == 2
    blue_low = int(blue_range_parts[0])
    blue_high = int(blue_range_parts[1])
    assert 0 <= blue_low <= blue_high <= 100
    
    red_range_parts = result.final_prediction.red_range.replace(" %", "").split(" – ")
    assert len(red_range_parts) == 2
    red_low = int(red_range_parts[0])
    red_high = int(red_range_parts[1])
    assert 0 <= red_low <= red_high <= 100
    
    # Validate model version
    assert len(result.model_version) > 0
    assert len(result.calibration_note) > 0


def test_fallback_builder_empty_draft():
    """Test fallback builder with empty/incomplete draft"""
    service = DraftIQV2Service()
    
    prediction_result = {
        "blue_win_prob": 0.5,
        "blue_win_prob_calibrated": 0.5,
        "confidence": 0.0,
        "model_version": "mid-xgb-unknown"
    }
    
    named_features = {"comp_features": {}}
    
    # Test with -1 (empty slots)
    result = service._build_fallback_analysis(
        elo="high",
        patch="15.21",
        blue_picks=[-1, -1, -1, -1, -1],
        red_picks=[-1, -1, -1, -1, -1],
        blue_bans=[],
        red_bans=[],
        prediction_result=prediction_result,
        named_features=named_features
    )
    
    # Should still return valid structure
    assert result.elo_context == "High"
    assert result.patch == "15.21"
    # May have empty items lists for incomplete drafts
    assert isinstance(result.blue_overview.items, list)
    assert isinstance(result.red_overview.items, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

