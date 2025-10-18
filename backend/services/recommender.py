"""
Smart pick recommendation service - suggests optimal champion picks based on current draft state
"""

import logging
import hashlib
import json
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

import numpy as np

from backend.services.inference import inference_service
from backend.config import settings

logger = logging.getLogger(__name__)


# ELO skill cap adjustments
ELO_SKILL_WEIGHTS = {
    'low': -0.3,   # Low elo: penalize mechanically complex champions
    'mid': 0.0,    # Mid elo: neutral
    'high': 0.2,   # High elo: reward high skill cap champions
}


class RecommenderService:
    """Service for champion pick/ban recommendations"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_max_size = 1000
    
    def _get_cache_key(self, elo: str, side: str, draft: Dict) -> str:
        """Generate cache key from draft state"""
        # Create deterministic hash of draft state
        draft_str = json.dumps(draft, sort_keys=True)
        hash_obj = hashlib.md5(f"{elo}:{side}:{draft_str}".encode())
        return hash_obj.hexdigest()
    
    def _get_available_champions(self, draft: Dict) -> List[int]:
        """Get list of champion IDs not yet picked or banned"""
        # Initialize inference service to get feature map
        if not inference_service._initialized:
            inference_service.initialize()
        
        feature_map = inference_service.feature_map
        if not feature_map:
            raise ValueError("Feature map not loaded")
        
        # All champion IDs
        all_champs = set(feature_map['champ_index'].values())
        
        # Extract picked and banned champions
        picked = set()
        banned = set()
        
        # Blue team picks
        for role in ['top', 'jungle', 'mid', 'adc', 'support']:
            if draft['blue'].get(role):
                picked.add(draft['blue'][role])
        
        # Red team picks
        for role in ['top', 'jungle', 'mid', 'adc', 'support']:
            if draft['red'].get(role):
                picked.add(draft['red'][role])
        
        # Bans
        banned.update(draft['blue'].get('bans', []))
        banned.update(draft['red'].get('bans', []))
        
        # Available champions
        available = all_champs - picked - banned
        return sorted(list(available))
    
    def _get_baseline_winrate(
        self,
        elo: str,
        patch: str,
        draft: Dict
    ) -> float:
        """Get current draft win probability (blue team perspective)"""
        # Extract current picks (may be incomplete)
        blue_picks = []
        red_picks = []
        
        for role in ['top', 'jungle', 'mid', 'adc', 'support']:
            blue_picks.append(draft['blue'].get(role, -1))
            red_picks.append(draft['red'].get(role, -1))
        
        # If any team is incomplete, return 50% baseline
        if -1 in blue_picks or -1 in red_picks:
            return 0.5
        
        try:
            result = inference_service.predict_draft(
                elo=elo,
                patch=patch,
                blue_picks=blue_picks,
                red_picks=red_picks,
                blue_bans=draft['blue'].get('bans', []),
                red_bans=draft['red'].get('bans', [])
            )
            return result['blue_win_prob']
        except Exception as e:
            logger.warning(f"Failed to get baseline winrate: {e}")
            return 0.5
    
    def _simulate_pick(
        self,
        elo: str,
        patch: str,
        draft: Dict,
        side: str,
        role: str,
        champion_id: int
    ) -> float:
        """Simulate adding a champion and return new win probability"""
        # Create test draft
        test_draft = {
            'blue': dict(draft['blue']),
            'red': dict(draft['red']),
        }
        
        # Add champion to specified role
        test_draft[side][role] = champion_id
        
        # Extract picks
        blue_picks = []
        red_picks = []
        
        for r in ['top', 'jungle', 'mid', 'adc', 'support']:
            blue_picks.append(test_draft['blue'].get(r, -1))
            red_picks.append(test_draft['red'].get(r, -1))
        
        # If still incomplete, can't predict
        if -1 in blue_picks or -1 in red_picks:
            return 0.5
        
        try:
            result = inference_service.predict_draft(
                elo=elo,
                patch=patch,
                blue_picks=blue_picks,
                red_picks=red_picks,
                blue_bans=draft['blue'].get('bans', []),
                red_bans=draft['red'].get('bans', [])
            )
            return result['blue_win_prob']
        except Exception as e:
            logger.warning(f"Failed to simulate pick {champion_id}: {e}")
            return 0.5
    
    def _get_champion_skill_cap(self, champion_id: int) -> float:
        """Get champion skill cap rating (0-1 scale)"""
        feature_map = inference_service.feature_map
        if not feature_map:
            return 0.5
        
        # Get champion tags
        tags = feature_map.get('tags', {}).get(str(champion_id), {})
        
        # Use mobility, utility, and damage complexity as proxy for skill cap
        mobility = tags.get('mobility', 0)
        utility = tags.get('utility', 0)
        
        # High mobility + utility typically = higher skill cap
        skill_cap = (mobility + utility) / 6.0  # Normalize to 0-1
        return min(max(skill_cap, 0.0), 1.0)
    
    def _get_champion_name(self, champion_id: int) -> str:
        """Get champion name from ID"""
        feature_map = inference_service.feature_map
        if not feature_map:
            return f"Champion_{champion_id}"
        
        # Reverse lookup in champ_index
        for name, cid in feature_map.get('champ_index', {}).items():
            if cid == champion_id:
                return name
        
        return f"Champion_{champion_id}"
    
    def _generate_pick_explanation(
        self,
        champion_id: int,
        elo: str,
        side: str,
        win_gain: float
    ) -> List[str]:
        """Generate human-readable reasons for pick recommendation"""
        feature_map = inference_service.feature_map
        if not feature_map:
            return ["Strategic advantage"]
        
        tags = feature_map.get('tags', {}).get(str(champion_id), {})
        reasons = []
        
        # Engagement/frontline
        engage = tags.get('engage', 0)
        if engage >= 2:
            reasons.append("+Strong engage")
        elif engage >= 1:
            reasons.append("+Frontline presence")
        
        # Damage type
        damage = tags.get('damage', [])
        if isinstance(damage, str):
            damage = [damage]
        if 'AP' in damage and 'AD' in damage:
            reasons.append("+Mixed damage")
        elif 'AP' in damage:
            reasons.append("+AP threat")
        
        # CC
        cc = tags.get('hard_cc', 0)
        if cc >= 2:
            reasons.append("+Crowd control")
        
        # Mobility
        mobility = tags.get('mobility', 0)
        if mobility >= 2:
            reasons.append("+High mobility")
        
        # Utility
        utility = tags.get('utility', 0)
        if utility >= 2:
            reasons.append("+Team utility")
        
        # Sustain
        sustain = tags.get('sustain', 0)
        if sustain >= 2:
            reasons.append("+Sustain/healing")
        
        # Poke
        poke = tags.get('poke', 0)
        if poke >= 1:
            reasons.append("+Poke power")
        
        # Early/late game
        early = tags.get('early', 0)
        late = tags.get('late', 0)
        if early >= 2:
            reasons.append("+Early power spike")
        elif late >= 2:
            reasons.append("+Late game scaling")
        
        # If no specific reasons, add generic
        if not reasons:
            if win_gain > 0.03:
                reasons.append("+Composition synergy")
            else:
                reasons.append("+Balanced pick")
        
        return reasons[:3]  # Max 3 reasons
    
    def recommend_next_pick(
        self,
        elo: str,
        side: str,
        draft: Dict,
        role: str,
        patch: str = '15.20',
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend top N champions for next pick.
        
        Args:
            elo: ELO group ('low', 'mid', 'high')
            side: Team side ('blue' or 'red')
            draft: Current draft state with blue/red picks and bans
            role: Role to fill ('top', 'jungle', 'mid', 'adc', 'support')
            patch: Patch version
            top_n: Number of recommendations to return
        
        Returns:
            Dictionary with recommendations and metadata
        """
        # Check cache
        cache_key = self._get_cache_key(elo, f"{side}:{role}", draft)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for recommendation: {elo} {side} {role}")
            return self._cache[cache_key]
        
        logger.info(f"Generating recommendations for {side} {role} at {elo} ELO")
        
        # Get available champions
        available = self._get_available_champions(draft)
        logger.info(f"Found {len(available)} available champions")
        
        if len(available) == 0:
            return {
                'side': side,
                'role': role,
                'recommendations': [],
                'model_version': f'{elo}-recommender',
                'message': 'No champions available'
            }
        
        # Get baseline winrate
        baseline = self._get_baseline_winrate(elo, patch, draft)
        
        # Calculate win gain for each available champion
        recommendations = []
        
        for champ_id in available[:100]:  # Limit to 100 for performance
            try:
                # Simulate pick
                new_prob = self._simulate_pick(elo, patch, draft, side, role, champ_id)
                
                # Calculate gain (from perspective of picking team)
                if side == 'blue':
                    win_gain = new_prob - baseline
                else:
                    win_gain = (1 - new_prob) - (1 - baseline)
                
                # Apply ELO skill cap adjustment
                skill_cap = self._get_champion_skill_cap(champ_id)
                elo_weight = ELO_SKILL_WEIGHTS.get(elo, 0.0)
                adjusted_gain = win_gain + (elo_weight * skill_cap / 3.0)
                
                # Get champion info
                champ_name = self._get_champion_name(champ_id)
                reasons = self._generate_pick_explanation(champ_id, elo, side, adjusted_gain)
                
                recommendations.append({
                    'champion_id': champ_id,
                    'champion_name': champ_name,
                    'win_gain': round(adjusted_gain, 4),
                    'raw_win_gain': round(win_gain, 4),
                    'reasons': reasons
                })
            
            except Exception as e:
                logger.warning(f"Failed to evaluate champion {champ_id}: {e}")
                continue
        
        # Sort by adjusted win gain
        recommendations.sort(key=lambda x: x['win_gain'], reverse=True)
        
        # Take top N
        top_recommendations = recommendations[:top_n]
        
        result = {
            'side': side,
            'role': role,
            'baseline_winrate': round(baseline, 4),
            'recommendations': top_recommendations,
            'model_version': f'{elo}-xgb-recommender',
            'elo': elo,
            'evaluated_champions': len(recommendations)
        }
        
        # Cache result
        if len(self._cache) >= self._cache_max_size:
            # Simple LRU: remove oldest
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = result
        
        return result
    
    def recommend_bans(
        self,
        elo: str,
        side: str,
        draft: Dict,
        patch: str = '15.20',
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend top N champions to ban.
        
        Simulates enemy picking each champion and finds which ones
        hurt your winrate the most.
        """
        cache_key = self._get_cache_key(elo, f"{side}:ban", draft)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for ban recommendation: {elo} {side}")
            return self._cache[cache_key]
        
        logger.info(f"Generating ban recommendations for {side} at {elo} ELO")
        
        # Get available champions
        available = self._get_available_champions(draft)
        
        if len(available) == 0:
            return {
                'side': side,
                'recommendations': [],
                'model_version': f'{elo}-recommender',
                'message': 'No champions available'
            }
        
        # Determine which role to test (first empty enemy role)
        enemy_side = 'red' if side == 'blue' else 'blue'
        test_role = None
        
        for role in ['top', 'jungle', 'mid', 'adc', 'support']:
            if not draft[enemy_side].get(role):
                test_role = role
                break
        
        if not test_role:
            # All enemy roles filled, simulate any role
            test_role = 'mid'
        
        # Get baseline
        baseline = self._get_baseline_winrate(elo, patch, draft)
        
        # Calculate threat level for each champion
        ban_recommendations = []
        
        for champ_id in available[:80]:  # Limit for performance
            try:
                # Simulate enemy picking this champion
                enemy_prob = self._simulate_pick(elo, patch, draft, enemy_side, test_role, champ_id)
                
                # Calculate how much it hurts us (from our perspective)
                if side == 'blue':
                    threat = baseline - enemy_prob  # How much we lose if they pick it
                else:
                    threat = (1 - baseline) - (1 - enemy_prob)
                
                champ_name = self._get_champion_name(champ_id)
                reasons = self._generate_pick_explanation(champ_id, elo, enemy_side, threat)
                
                # Reframe reasons as threats
                threat_reasons = [r.replace('+', 'Enemy ') for r in reasons]
                
                ban_recommendations.append({
                    'champion_id': champ_id,
                    'champion_name': champ_name,
                    'threat_level': round(threat, 4),
                    'reasons': threat_reasons
                })
            
            except Exception as e:
                logger.warning(f"Failed to evaluate ban {champ_id}: {e}")
                continue
        
        # Sort by threat level
        ban_recommendations.sort(key=lambda x: x['threat_level'], reverse=True)
        
        result = {
            'side': side,
            'recommendations': ban_recommendations[:top_n],
            'model_version': f'{elo}-xgb-recommender',
            'elo': elo,
            'evaluated_champions': len(ban_recommendations)
        }
        
        # Cache
        if len(self._cache) >= self._cache_max_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = result
        
        return result


# Global recommender service
recommender_service = RecommenderService()


