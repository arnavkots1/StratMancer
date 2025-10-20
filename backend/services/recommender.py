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
        
        # For empty drafts, add timestamp to avoid persistent caching
        is_empty_draft = all(
            draft['blue'].get(role) is None and draft['red'].get(role) is None
            for role in ['top', 'jgl', 'mid', 'adc', 'sup']
        )
        
        if is_empty_draft:
            import time
            timestamp = int(time.time() / 60)  # Cache for 1 minute for empty drafts
            hash_obj = hashlib.md5(f"{elo}:{side}:{draft_str}:{timestamp}".encode())
        else:
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
        for role in ['top', 'jgl', 'mid', 'adc', 'sup']:
            champ_id = draft['blue'].get(role)
            # Check for valid champion ID (not None, not -1, not 0, not undefined)
            if champ_id and champ_id != -1:
                picked.add(champ_id)
        
        # Red team picks
        for role in ['top', 'jgl', 'mid', 'adc', 'sup']:
            champ_id = draft['red'].get(role)
            # Check for valid champion ID (not None, not -1, not 0, not undefined)
            if champ_id and champ_id != -1:
                picked.add(champ_id)
        
        # Bans - ensure they are integers
        blue_bans = draft['blue'].get('bans', [])
        red_bans = draft['red'].get('bans', [])
        
        logger.info(f"Raw blue bans: {blue_bans}")
        logger.info(f"Raw red bans: {red_bans}")
        
        # Convert to integers and filter out None/invalid values
        for ban_id in blue_bans:
            if ban_id is not None and ban_id != -1:
                try:
                    banned.add(int(ban_id))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid ban ID: {ban_id}")
        
        for ban_id in red_bans:
            if ban_id is not None and ban_id != -1:
                try:
                    banned.add(int(ban_id))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid ban ID: {ban_id}")
        
        # Available champions
        available = all_champs - picked - banned
        
        # Debug logging
        logger.info(f"Picked champions: {sorted(list(picked))}")
        logger.info(f"Banned champions: {sorted(list(banned))}")
        logger.info(f"Available champions: {len(available)} total")
        
        # Check for any champions that appear in both banned and available (debugging)
        overlap = banned.intersection(available)
        if overlap:
            logger.warning(f"Champions incorrectly in both banned and available: {sorted(list(overlap))}")
        else:
            logger.info("No overlap between banned and available champions")
        
        # Check specifically for Vayne to catch mapping issues between front and backend
        vayne_id = feature_map.get('champ_index', {}).get('Vayne')
        if vayne_id is not None:
            if vayne_id in banned:
                logger.info(f"Vayne (ID {vayne_id}) is correctly in banned list")
            else:
                logger.info(f"Vayne (ID {vayne_id}) is not in banned list (expected if not banned)")
            
            if vayne_id in available:
                logger.info(f"Vayne (ID {vayne_id}) is available for selection")
            else:
                logger.info(f"Vayne (ID {vayne_id}) is not available (banned or picked)")
        
        return sorted(list(available))
    
    def _get_baseline_winrate(
        self,
        elo: str,
        patch: str,
        draft: Dict
    ) -> float:
        """Get current draft win probability (blue team perspective)"""
        try:
            # Use the role-aware prediction method for partial drafts
            result = inference_service.predict_draft_with_roles(
                elo=elo,
                patch=patch,
                blue_draft=draft['blue'],
                red_draft=draft['red']
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
        
        try:
            # Use the new role-aware prediction method
            result = inference_service.predict_draft_with_roles(
                elo=elo,
                patch=patch,
                blue_draft=test_draft['blue'],
                red_draft=test_draft['red']
            )
            # print(f"DEBUG: predict_draft result for champ {champion_id}: {result}")
            return result['blue_win_prob']
        except Exception as e:
            logger.warning(f"Failed to simulate pick {champion_id}: {e}")
            return 0.5
    
    def _get_champion_skill_cap(self, champion_id: int) -> float:
        """Get champion skill cap rating (0-1 scale)"""
        feature_map = inference_service.feature_map
        if not feature_map:
            logger.warning("No feature map available for skill cap calculation")
            return 0.5
        
        # Get champion tags
        tags = feature_map.get('tags', {}).get(str(champion_id), {})
        
        # Use the skill_cap field directly (0-3 scale, normalize to 0-1)
        skill_cap = tags.get('skill_cap', 1)  # Default to 1 if not found
        result = skill_cap / 3.0  # Normalize from 0-3 to 0-1
        result = min(max(result, 0.0), 1.0)
        
        # logger.debug(f"Champ {champion_id}: skill_cap={skill_cap}, normalized={result}")
        return result
    
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
            role: Role to fill ('top', 'jgl', 'mid', 'adc', 'sup')
            patch: Patch version
            top_n: Number of recommendations to return
        
        Returns:
            Dictionary with recommendations and metadata
        """
        # Check cache
        # TEMPORARILY DISABLE ALL CACHING FOR DEBUGGING
        # cache_key = self._get_cache_key(elo, f"{side}:{role}", draft)
        # if cache_key in self._cache:
        #     logger.debug(f"Cache hit for recommendation: {elo} {side} {role}")
        #     return self._cache[cache_key]
        
        logger.info(f"Generating recommendations for {side} {role} at {elo} ELO")
        
        # Get available champions
        available = self._get_available_champions(draft)
        logger.info(f"Found {len(available)} available champions")
        
        # Debug: Log current draft state
        logger.debug(f"Current draft state: blue={draft['blue']}, red={draft['red']}")
        
        # Debug: Check if Annie (champion ID 1) is in available list
        annie_id = 1
        if annie_id in available:
            logger.warning(f"Annie (ID {annie_id}) is still available despite being picked!")
        else:
            logger.debug(f"Annie (ID {annie_id}) correctly excluded from available champions")
        
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
        
        # For empty drafts, use champion popularity/strength as proxy
        is_empty_draft = all(
            draft['blue'].get(role) is None and draft['red'].get(role) is None
            for role in ['top', 'jgl', 'mid', 'adc', 'sup']
        )
        
        # Build exclusion set: all picked champs and both teams' bans
        excluded: set[int] = set()
        for r in ['top', 'jgl', 'mid', 'adc', 'sup']:
            v = draft['blue'].get(r)
            if v is not None and v != -1:
                excluded.add(int(v))
            v = draft['red'].get(r)
            if v is not None and v != -1:
                excluded.add(int(v))
        for b in (draft['blue'].get('bans', []) or []):
            try:
                if b is not None and b != -1:
                    excluded.add(int(b))
            except Exception:
                pass
        for b in (draft['red'].get('bans', []) or []):
            try:
                if b is not None and b != -1:
                    excluded.add(int(b))
            except Exception:
                pass

        # Calculate win gain for each available champion
        recommendations = []
        
        for champ_id in available[:100]:  # Limit to 100 for performance
            if int(champ_id) in excluded:
                continue
            try:
                if is_empty_draft:
                    # For empty drafts, use champion strength as proxy
                    skill_cap = self._get_champion_skill_cap(champ_id)
                    elo_weight = ELO_SKILL_WEIGHTS.get(elo, 0.0)
                    
                    # Base strength from skill cap and role suitability
                    base_strength = skill_cap * 0.1  # 0-0.1 range
                    elo_adjustment = elo_weight * skill_cap / 10.0  # Smaller adjustment
                    adjusted_gain = base_strength + elo_adjustment
                    
                    # Add some randomness to differentiate champions
                    import random
                    adjusted_gain += random.uniform(-0.02, 0.02)
                else:
                    # Simulate pick
                    new_prob = self._simulate_pick(elo, patch, draft, side, role, champ_id)
                    
                    # Calculate gain (from perspective of picking team)
                    if side == 'blue':
                        win_gain = new_prob - baseline
                    else:
                        win_gain = (1 - new_prob) - (1 - baseline)
                    
                    # Debug logging for first few champions
                    if len(recommendations) < 3:
                        champ_name = self._get_champion_name(champ_id)
                        logger.info(f"Champion {champ_name} (ID {champ_id}): baseline={baseline:.4f}, new_prob={new_prob:.4f}, win_gain={win_gain:.4f}")
                    
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
                    'raw_win_gain': round(adjusted_gain, 4) if is_empty_draft else round(win_gain, 4),
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
        
        # TEMPORARILY DISABLE ALL CACHING FOR DEBUGGING
        # if len(self._cache) >= self._cache_max_size:
        #     # Simple LRU: remove oldest
        #     self._cache.pop(next(iter(self._cache)))
        # self._cache[cache_key] = result
        
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
        # Check if this is an empty draft
        is_empty_draft = all(
            draft['blue'].get(role) is None and draft['red'].get(role) is None
            for role in ['top', 'jgl', 'mid', 'adc', 'sup']
        )
        
        # TEMPORARILY DISABLE ALL CACHING FOR DEBUGGING
        # if not is_empty_draft:
        #     cache_key = self._get_cache_key(elo, f"{side}:ban", draft)
        #     if cache_key in self._cache:
        #         logger.debug(f"Cache hit for ban recommendation: {elo} {side}")
        #         return self._cache[cache_key]
        
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
        
        for role in ['top', 'jgl', 'mid', 'adc', 'sup']:
            if not draft[enemy_side].get(role):
                test_role = role
                break
        
        if not test_role:
            # All enemy roles filled, simulate any role
            test_role = 'mid'
        
        # Get baseline
        baseline = self._get_baseline_winrate(elo, patch, draft)
        
        # is_empty_draft already determined above
        
        # logger.info(f"Empty draft detected: {is_empty_draft}")
        
        # Build exclusion set: all picked champs and both teams' bans
        excluded: set[int] = set()
        for r in ['top', 'jgl', 'mid', 'adc', 'sup']:
            v = draft['blue'].get(r)
            if v is not None and v != -1:
                excluded.add(int(v))
            v = draft['red'].get(r)
            if v is not None and v != -1:
                excluded.add(int(v))
        for b in (draft['blue'].get('bans', []) or []):
            try:
                if b is not None and b != -1:
                    excluded.add(int(b))
            except Exception:
                pass
        for b in (draft['red'].get('bans', []) or []):
            try:
                if b is not None and b != -1:
                    excluded.add(int(b))
            except Exception:
                pass

        # Calculate threat level for each champion
        ban_recommendations = []
        
        for champ_id in available[:80]:  # Limit for performance
            if int(champ_id) in excluded:
                continue
            try:
                if is_empty_draft:
                    # For empty drafts, use champion strength as proxy for threat
                    skill_cap = self._get_champion_skill_cap(champ_id)
                    elo_weight = ELO_SKILL_WEIGHTS.get(elo, 0.0)
                    
                    # Base threat from skill cap (higher skill cap = more dangerous)
                    base_threat = skill_cap * 0.08  # 0-0.08 range
                    elo_adjustment = elo_weight * skill_cap / 15.0  # Smaller adjustment
                    threat = base_threat + elo_adjustment
                    
                    # Add some randomness to differentiate champions
                    import random
                    threat += random.uniform(-0.015, 0.015)
                    
                    # logger.info(f"Champ {champ_id}: skill_cap={skill_cap}, base_threat={base_threat}, final_threat={threat}")
                else:
                    # TEMPORARY FIX: Use skill cap approach for all non-empty drafts
                    # The ML model is predicting extreme values (0.0% or 100%), so we'll use
                    # skill cap as a proxy until the model is retrained with better data
                    
                    skill_cap = self._get_champion_skill_cap(champ_id)
                    elo_weight = ELO_SKILL_WEIGHTS.get(elo, 0.0)
                    
                    # Base threat from skill cap (higher skill cap = more dangerous)
                    base_threat = skill_cap * 0.07  # 0-0.07 range for non-empty drafts
                    elo_adjustment = elo_weight * skill_cap / 18.0
                    threat = base_threat + elo_adjustment
                    
                    # Add some randomness to differentiate champions
                    import random
                    threat += random.uniform(-0.012, 0.012)
                
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
        
        # TEMPORARILY DISABLE ALL CACHING FOR DEBUGGING
        # if not is_empty_draft:
        #     cache_key = self._get_cache_key(elo, f"{side}:ban", draft)
        #     if len(self._cache) >= self._cache_max_size:
        #         self._cache.pop(next(iter(self._cache)))
        #     self._cache[cache_key] = result
        
        return result


# Global recommender service
recommender_service = RecommenderService()

