"""
Unit tests for schema validation.
"""
import pytest
from pydantic import ValidationError

from src.transformers.schema import (
    MatchData, ChampionStats, Objectives, DerivedFeatures
)


def test_champion_stats_valid():
    """Test valid champion stats creation"""
    stats = ChampionStats(
        id=1,
        role="MID",
        kda=3.5,
        cs=7.8,
        dmg_share=0.25,
        gold_share=0.22
    )
    assert stats.id == 1
    assert stats.kda == 3.5
    assert stats.cs == 7.8


def test_champion_stats_negative_kda():
    """Test that negative KDA is converted to 0"""
    stats = ChampionStats(
        id=1,
        role="TOP",
        kda=-1.0,
        cs=5.0,
        dmg_share=0.2,
        gold_share=0.2
    )
    assert stats.kda == 0.0


def test_objectives_valid():
    """Test valid objectives creation"""
    obj = Objectives(dragons=3, heralds=1, barons=2, towers=8)
    assert obj.dragons == 3
    assert obj.barons == 2


def test_objectives_negative_fails():
    """Test that negative objectives fail validation"""
    with pytest.raises(ValidationError):
        Objectives(dragons=-1, heralds=0, barons=0, towers=0)


def test_derived_features_valid():
    """Test valid derived features"""
    features = DerivedFeatures(
        ap_ad_ratio=0.6,
        engage_score=7.5,
        splitpush_score=5.0,
        teamfight_synergy=0.75
    )
    assert features.ap_ad_ratio == 0.6
    assert features.teamfight_synergy == 0.75


def test_match_data_valid():
    """Test complete valid match data"""
    champion_stats = [
        ChampionStats(id=i, role="MID", kda=3.0, cs=7.0, dmg_share=0.2, gold_share=0.2)
        for i in range(1, 11)
    ]
    
    match = MatchData(
        match_id="NA1_123456",
        patch="14.1",
        elo_rank="GOLD",
        blue_picks=[1, 2, 3, 4, 5],
        red_picks=[6, 7, 8, 9, 10],
        blue_bans=[11, 12, 13, 14, 15],
        red_bans=[16, 17, 18, 19, 20],
        blue_win=True,
        champion_stats=champion_stats,
        blue_objectives=Objectives(dragons=3, heralds=1, barons=1, towers=8),
        red_objectives=Objectives(dragons=1, heralds=0, barons=0, towers=3),
        derived_features=DerivedFeatures(
            ap_ad_ratio=0.5,
            engage_score=7.0,
            splitpush_score=5.0,
            teamfight_synergy=0.7
        )
    )
    
    assert match.match_id == "NA1_123456"
    assert match.blue_win is True
    assert len(match.champion_stats) == 10


def test_match_data_invalid_rank():
    """Test that invalid rank fails validation"""
    champion_stats = [
        ChampionStats(id=i, role="MID", kda=3.0, cs=7.0, dmg_share=0.2, gold_share=0.2)
        for i in range(1, 11)
    ]
    
    with pytest.raises(ValidationError):
        MatchData(
            match_id="NA1_123456",
            patch="14.1",
            elo_rank="INVALID_RANK",  # Invalid rank
            blue_picks=[1, 2, 3, 4, 5],
            red_picks=[6, 7, 8, 9, 10],
            blue_bans=[11, 12, 13, 14, 15],
            red_bans=[16, 17, 18, 19, 20],
            blue_win=True,
            champion_stats=champion_stats,
            blue_objectives=Objectives(dragons=3, heralds=1, barons=1, towers=8),
            red_objectives=Objectives(dragons=1, heralds=0, barons=0, towers=3),
            derived_features=DerivedFeatures(
                ap_ad_ratio=0.5,
                engage_score=7.0,
                splitpush_score=5.0,
                teamfight_synergy=0.7
            )
        )


def test_match_data_duplicate_picks():
    """Test that duplicate picks fail validation"""
    champion_stats = [
        ChampionStats(id=i, role="MID", kda=3.0, cs=7.0, dmg_share=0.2, gold_share=0.2)
        for i in range(1, 11)
    ]
    
    with pytest.raises(ValidationError):
        MatchData(
            match_id="NA1_123456",
            patch="14.1",
            elo_rank="GOLD",
            blue_picks=[1, 1, 3, 4, 5],  # Duplicate
            red_picks=[6, 7, 8, 9, 10],
            blue_bans=[11, 12, 13, 14, 15],
            red_bans=[16, 17, 18, 19, 20],
            blue_win=True,
            champion_stats=champion_stats,
            blue_objectives=Objectives(dragons=3, heralds=1, barons=1, towers=8),
            red_objectives=Objectives(dragons=1, heralds=0, barons=0, towers=3),
            derived_features=DerivedFeatures(
                ap_ad_ratio=0.5,
                engage_score=7.0,
                splitpush_score=5.0,
                teamfight_synergy=0.7
            )
        )


def test_match_data_wrong_champion_count():
    """Test that wrong number of champion stats fails"""
    champion_stats = [
        ChampionStats(id=i, role="MID", kda=3.0, cs=7.0, dmg_share=0.2, gold_share=0.2)
        for i in range(1, 6)  # Only 5 instead of 10
    ]
    
    with pytest.raises(ValidationError):
        MatchData(
            match_id="NA1_123456",
            patch="14.1",
            elo_rank="GOLD",
            blue_picks=[1, 2, 3, 4, 5],
            red_picks=[6, 7, 8, 9, 10],
            blue_bans=[11, 12, 13, 14, 15],
            red_bans=[16, 17, 18, 19, 20],
            blue_win=True,
            champion_stats=champion_stats,
            blue_objectives=Objectives(dragons=3, heralds=1, barons=1, towers=8),
            red_objectives=Objectives(dragons=1, heralds=0, barons=0, towers=3),
            derived_features=DerivedFeatures(
                ap_ad_ratio=0.5,
                engage_score=7.0,
                splitpush_score=5.0,
                teamfight_synergy=0.7
            )
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

