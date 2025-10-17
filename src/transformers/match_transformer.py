"""
Transform raw Riot API match data into our standardized schema.
"""
import logging
from typing import Dict, List, Optional
from .schema import MatchData, ChampionStats, Objectives, DerivedFeatures

logger = logging.getLogger(__name__)


class MatchTransformer:
    """Transforms raw match data into standardized schema"""
    
    # Role mapping for position
    ROLE_MAP = {
        'TOP': 'TOP',
        'JUNGLE': 'JUNGLE',
        'MIDDLE': 'MID',
        'BOTTOM': 'ADC',
        'UTILITY': 'SUPPORT'
    }
    
    def __init__(self):
        """Initialize transformer"""
        pass
    
    def transform(self, raw_match: Dict, elo_rank: str) -> Optional[MatchData]:
        """
        Transform raw match data to standardized schema.
        
        Args:
            raw_match: Raw match data from Riot API
            elo_rank: Rank tier for this match
            
        Returns:
            MatchData object or None if transformation fails
        """
        try:
            info = raw_match.get('info', {})
            metadata = raw_match.get('metadata', {})
            
            # Extract basic info
            match_id = metadata.get('matchId', '')
            patch = self._extract_patch(info.get('gameVersion', ''))
            
            # Extract teams
            teams = {team['teamId']: team for team in info.get('teams', [])}
            blue_team = teams.get(100, {})
            red_team = teams.get(200, {})
            
            # Extract participants
            participants = info.get('participants', [])
            blue_participants = [p for p in participants if p['teamId'] == 100]
            red_participants = [p for p in participants if p['teamId'] == 200]
            
            # Validate we have 5v5
            if len(blue_participants) != 5 or len(red_participants) != 5:
                logger.warning(f"Invalid team sizes for match {match_id}")
                return None
            
            # Extract picks and bans
            blue_picks = [p['championId'] for p in blue_participants]
            red_picks = [p['championId'] for p in red_participants]
            
            blue_bans = self._extract_bans(blue_team)
            red_bans = self._extract_bans(red_team)
            
            # Determine winner
            blue_win = blue_team.get('win', False)
            
            # Extract champion stats
            champion_stats = self._extract_champion_stats(participants)
            
            # Extract objectives
            blue_objectives = self._extract_objectives(blue_team.get('objectives', {}))
            red_objectives = self._extract_objectives(red_team.get('objectives', {}))
            
            # Calculate derived features
            derived_features = self._calculate_derived_features(
                blue_participants, red_participants, info
            )
            
            # Create match data
            match_data = MatchData(
                match_id=match_id,
                patch=patch,
                elo_rank=elo_rank.upper(),
                blue_picks=blue_picks,
                red_picks=red_picks,
                blue_bans=blue_bans,
                red_bans=red_bans,
                blue_win=blue_win,
                champion_stats=champion_stats,
                blue_objectives=blue_objectives,
                red_objectives=red_objectives,
                derived_features=derived_features
            )
            
            return match_data
            
        except Exception as e:
            logger.error(f"Failed to transform match: {e}", exc_info=True)
            return None
    
    def _extract_patch(self, game_version: str) -> str:
        """Extract major.minor patch from game version"""
        try:
            parts = game_version.split('.')
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
        except:
            pass
        return "unknown"
    
    def _extract_bans(self, team: Dict) -> List[int]:
        """Extract 5 bans from team data"""
        bans = team.get('bans', [])
        ban_ids = [ban.get('championId', -1) for ban in bans]
        
        # Ensure we have exactly 5 bans (pad with -1 if needed)
        while len(ban_ids) < 5:
            ban_ids.append(-1)
        
        return ban_ids[:5]
    
    def _extract_champion_stats(self, participants: List[Dict]) -> List[ChampionStats]:
        """Extract stats for all champions"""
        stats = []
        
        for p in participants:
            try:
                # Calculate KDA
                kills = p.get('kills', 0)
                deaths = p.get('deaths', 0)
                assists = p.get('assists', 0)
                kda = (kills + assists) / max(deaths, 1)
                
                # CS per minute
                total_cs = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
                game_duration_minutes = p.get('timePlayed', 1800) / 60.0
                cs_per_min = total_cs / max(game_duration_minutes, 1)
                
                # Role
                role = self.ROLE_MAP.get(p.get('teamPosition', ''), 'UNKNOWN')
                
                stats.append(ChampionStats(
                    id=p.get('championId', 0),
                    role=role,
                    kda=kda,
                    cs=cs_per_min,
                    dmg_share=0.0,  # Will calculate below
                    gold_share=0.0  # Will calculate below
                ))
            except Exception as e:
                logger.warning(f"Failed to extract champion stats: {e}")
                continue
        
        # Calculate shares
        self._calculate_shares(participants, stats)
        
        return stats
    
    def _calculate_shares(self, participants: List[Dict], stats: List[ChampionStats]):
        """Calculate damage and gold shares for each team"""
        # Group by team
        blue_participants = [p for p in participants if p['teamId'] == 100]
        red_participants = [p for p in participants if p['teamId'] == 200]
        blue_stats = stats[:5]
        red_stats = stats[5:]
        
        # Calculate blue team shares
        self._calculate_team_shares(blue_participants, blue_stats)
        
        # Calculate red team shares
        self._calculate_team_shares(red_participants, red_stats)
    
    def _calculate_team_shares(self, participants: List[Dict], stats: List[ChampionStats]):
        """Calculate shares for a single team"""
        total_damage = sum(p.get('totalDamageDealtToChampions', 0) for p in participants)
        total_gold = sum(p.get('goldEarned', 0) for p in participants)
        
        for i, p in enumerate(participants):
            if i < len(stats):
                damage = p.get('totalDamageDealtToChampions', 0)
                gold = p.get('goldEarned', 0)
                
                stats[i].dmg_share = damage / max(total_damage, 1)
                stats[i].gold_share = gold / max(total_gold, 1)
    
    def _extract_objectives(self, objectives_data: Dict) -> Objectives:
        """Extract objectives from team data"""
        return Objectives(
            dragons=objectives_data.get('dragon', {}).get('kills', 0),
            heralds=objectives_data.get('riftHerald', {}).get('kills', 0),
            barons=objectives_data.get('baron', {}).get('kills', 0),
            towers=objectives_data.get('tower', {}).get('kills', 0)
        )
    
    def _calculate_derived_features(self, blue_team: List[Dict], 
                                    red_team: List[Dict], info: Dict) -> DerivedFeatures:
        """
        Calculate derived team composition features.
        These are simplified heuristics - can be enhanced with champion data.
        """
        # Calculate for blue team
        blue_ap_ad = self._calculate_ap_ad_ratio(blue_team)
        blue_engage = self._calculate_engage_score(blue_team)
        blue_splitpush = self._calculate_splitpush_score(blue_team)
        blue_teamfight = self._calculate_teamfight_synergy(blue_team)
        
        # For now, return blue team features
        # In production, you might want both teams' features
        return DerivedFeatures(
            ap_ad_ratio=blue_ap_ad,
            engage_score=blue_engage,
            splitpush_score=blue_splitpush,
            teamfight_synergy=blue_teamfight
        )
    
    def _calculate_ap_ad_ratio(self, team: List[Dict]) -> float:
        """
        Calculate AP to AD ratio based on damage types.
        Simplified: uses magic vs physical damage dealt.
        """
        total_magic = sum(p.get('magicDamageDealtToChampions', 0) for p in team)
        total_physical = sum(p.get('physicalDamageDealtToChampions', 0) for p in team)
        total_damage = total_magic + total_physical
        
        if total_damage == 0:
            return 0.5
        
        return total_magic / total_damage
    
    def _calculate_engage_score(self, team: List[Dict]) -> float:
        """
        Calculate engage potential based on CC and initiation.
        Simplified: uses CC time and total damage.
        """
        total_cc = sum(p.get('timeCCingOthers', 0) for p in team)
        
        # Normalize to 0-10 scale (rough heuristic)
        engage_score = min(total_cc / 60.0 * 10, 10.0)
        
        return engage_score
    
    def _calculate_splitpush_score(self, team: List[Dict]) -> float:
        """
        Calculate splitpush potential.
        Simplified: based on damage to objectives and structures.
        """
        total_structure_damage = sum(p.get('damageDealtToBuildings', 0) for p in team)
        total_objective_damage = sum(p.get('damageDealtToObjectives', 0) for p in team)
        
        total = total_structure_damage + total_objective_damage
        
        # Normalize to 0-10 scale
        splitpush_score = min(total / 50000.0 * 10, 10.0)
        
        return splitpush_score
    
    def _calculate_teamfight_synergy(self, team: List[Dict]) -> float:
        """
        Calculate teamfight synergy.
        Simplified: based on assist participation and damage consistency.
        """
        total_kills = sum(p.get('kills', 0) for p in team)
        total_assists = sum(p.get('assists', 0) for p in team)
        
        if total_kills == 0:
            return 0.5
        
        # High assists relative to kills indicates good teamfighting
        synergy = min((total_assists / (total_kills * 5)) / 2, 1.0)
        
        return synergy

