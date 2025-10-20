"""
Post-draft analysis service providing detailed insights on team compositions,
matchups, and strategic recommendations.
"""
import logging
from typing import Dict, List, Any, Optional
from backend.services.inference import inference_service

logger = logging.getLogger(__name__)


class DraftAnalyzer:
    """Provides comprehensive post-draft analysis"""
    
    def __init__(self):
        # Lazy reference; inference_service initializes feature map on demand
        self.feature_map = None

    def _ensure_feature_map(self) -> None:
        """Ensure feature map is loaded before accessing it."""
        if self.feature_map is not None:
            return
        # Initialize inference service (lazy) which loads feature map
        try:
            inference_service.initialize()
            self.feature_map = inference_service.feature_map
        except Exception:
            self.feature_map = None
        
    def analyze_draft(
        self,
        blue_team: Dict[str, int],
        red_team: Dict[str, int],
        blue_win_prob: float,
        red_win_prob: float,
        elo: str,
        patch: str
    ) -> Dict[str, Any]:
        """
        Comprehensive draft analysis after picks/bans are complete.
        
        Args:
            blue_team: Blue team picks (top, jgl, mid, adc, sup) and bans
            red_team: Red team picks (top, jgl, mid, adc, sup) and bans
            blue_win_prob: Predicted blue win probability
            red_win_prob: Predicted red win probability
            elo: ELO group (low/mid/high)
            patch: Game patch version
            
        Returns:
            Comprehensive analysis including matchups, win conditions, threats
        """
        try:
            # Ensure resources are available
            self._ensure_feature_map()
            if not self.feature_map:
                raise RuntimeError("Feature map not loaded")
            
            # Get champion data
            blue_picks = self._get_team_picks(blue_team)
            red_picks = self._get_team_picks(red_team)
            
            # Analyze team compositions
            blue_comp = self._analyze_team_composition(blue_picks, "blue")
            red_comp = self._analyze_team_composition(red_picks, "red")
            
            # Analyze lane matchups
            matchups = self._analyze_matchups(blue_picks, red_picks)
            
            # Generate win conditions
            blue_win_conditions = self._get_win_conditions(blue_comp, red_comp, "blue")
            red_win_conditions = self._get_win_conditions(red_comp, blue_comp, "red")
            
            # Identify key threats
            blue_threats = self._identify_threats(blue_picks, red_picks, "blue")
            red_threats = self._identify_threats(red_picks, blue_picks, "red")
            
            # Power spike analysis
            blue_power_spikes = self._analyze_power_spikes(blue_picks)
            red_power_spikes = self._analyze_power_spikes(red_picks)
            
            # Game plan
            game_plan = self._generate_game_plan(
                blue_comp, red_comp, blue_win_prob, elo
            )
            
            return {
                "summary": {
                    "blue_win_probability": blue_win_prob,
                    "red_win_probability": red_win_prob,
                    "favored_team": "blue" if blue_win_prob > 0.5 else "red",
                    "confidence": abs(blue_win_prob - 0.5) * 2,  # 0 to 1 scale
                    "elo_group": elo,
                    "patch": patch
                },
                "blue_team": {
                    "composition": blue_comp,
                    "win_conditions": blue_win_conditions,
                    "key_threats": blue_threats,
                    "power_spikes": blue_power_spikes,
                    "champions": blue_picks
                },
                "red_team": {
                    "composition": red_comp,
                    "win_conditions": red_win_conditions,
                    "key_threats": red_threats,
                    "power_spikes": red_power_spikes,
                    "champions": red_picks
                },
                "matchups": matchups,
                "game_plan": game_plan
            }
            
        except Exception as e:
            logger.error(f"Draft analysis failed: {e}", exc_info=True)
            return {
                "error": "Analysis failed",
                "message": str(e)
            }
    
    def _get_team_picks(self, team: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract and enrich champion data for team picks"""
        roles = ['top', 'jgl', 'mid', 'adc', 'sup']
        picks = {}
        
        for role in roles:
            champ_id = team.get(role)
            if champ_id and champ_id != -1:
                champ_data = self._get_champion_data(str(champ_id))
                if champ_data:
                    picks[role] = {
                        **champ_data,
                        "role": role.upper()
                    }
        
        return picks
    
    def _get_champion_data(self, champ_id: str) -> Optional[Dict[str, Any]]:
        """Get enriched champion data from feature map"""
        # Ensure feature map is available
        if self.feature_map is None:
            self._ensure_feature_map()
        if not self.feature_map:
            return None
        champ_data = self.feature_map.get('champions', {}).get(champ_id)
        if not champ_data:
            return None
            
        return {
            "id": champ_id,
            "name": champ_data.get('name', 'Unknown'),
            "title": champ_data.get('title', ''),
            "tags": champ_data.get('tags', {}),
            "stats": champ_data.get('stats', {}),
            "skill_cap": champ_data.get('skill_cap', 1)
        }
    
    def _analyze_team_composition(self, picks: Dict[str, Dict], team_side: str) -> Dict[str, Any]:
        """Analyze overall team composition strengths"""
        if not picks:
            return {}
        
        # Calculate damage profile
        ap_count = sum(1 for p in picks.values() if 'Mage' in p.get('tags', {}).get('class', []))
        ad_count = len(picks) - ap_count
        
        # Calculate engage potential
        engage_champs = sum(1 for p in picks.values() 
                          if any(tag in ['engage', 'initiator'] 
                                for tag in p.get('tags', {}).get('role', [])))
        
        # Calculate tankiness
        tank_champs = sum(1 for p in picks.values() 
                         if 'Tank' in p.get('tags', {}).get('class', []))
        
        # Calculate mobility
        mobile_champs = sum(1 for p in picks.values() 
                          if p.get('stats', {}).get('mobility', 0) >= 2)
        
        # Overall assessment
        composition_type = self._identify_comp_type(picks)
        
        return {
            "type": composition_type,
            "damage_profile": {
                "ap_champions": ap_count,
                "ad_champions": ad_count,
                "balance": "Balanced" if abs(ap_count - ad_count) <= 1 else "AD-heavy" if ad_count > ap_count else "AP-heavy"
            },
            "engage_potential": "High" if engage_champs >= 2 else "Medium" if engage_champs == 1 else "Low",
            "tankiness": "High" if tank_champs >= 2 else "Medium" if tank_champs == 1 else "Low",
            "mobility": "High" if mobile_champs >= 3 else "Medium" if mobile_champs >= 2 else "Low",
            "strengths": self._identify_comp_strengths(picks, composition_type),
            "weaknesses": self._identify_comp_weaknesses(picks, composition_type)
        }
    
    def _identify_comp_type(self, picks: Dict[str, Dict]) -> str:
        """Identify the primary composition archetype"""
        # Simple heuristic based on champion classes and roles
        engage_count = sum(1 for p in picks.values() 
                          if any(tag in ['engage', 'initiator'] 
                                for tag in p.get('tags', {}).get('role', [])))
        poke_count = sum(1 for p in picks.values() 
                        if 'poke' in p.get('tags', {}).get('role', []))
        splitpush_count = sum(1 for p in picks.values() 
                             if 'splitpush' in p.get('tags', {}).get('role', []))
        
        if engage_count >= 2:
            return "Teamfight/Engage"
        elif poke_count >= 2:
            return "Poke/Siege"
        elif splitpush_count >= 1:
            return "Split Push"
        else:
            return "Balanced/Skirmish"
    
    def _identify_comp_strengths(self, picks: Dict[str, Dict], comp_type: str) -> List[str]:
        """Identify team composition strengths"""
        strengths = []
        
        if "Teamfight" in comp_type:
            strengths.append("Strong 5v5 teamfighting")
            strengths.append("Good engage tools")
        elif "Poke" in comp_type:
            strengths.append("Long-range poke damage")
            strengths.append("Objective control")
        elif "Split Push" in comp_type:
            strengths.append("Side lane pressure")
            strengths.append("Map control")
        
        # Add generic strengths
        if any('Tank' in p.get('tags', {}).get('class', []) for p in picks.values()):
            strengths.append("Good frontline")
        
        return strengths[:3]  # Top 3 strengths
    
    def _identify_comp_weaknesses(self, picks: Dict[str, Dict], comp_type: str) -> List[str]:
        """Identify team composition weaknesses"""
        weaknesses = []
        
        # Check for squishy team
        tank_count = sum(1 for p in picks.values() if 'Tank' in p.get('tags', {}).get('class', []))
        if tank_count == 0:
            weaknesses.append("Lacks frontline/tankiness")
        
        # Check for engage
        engage_count = sum(1 for p in picks.values() 
                          if 'engage' in p.get('tags', {}).get('role', []))
        if engage_count == 0:
            weaknesses.append("Limited engage potential")
        
        # Check damage profile
        ap_count = sum(1 for p in picks.values() if 'Mage' in p.get('tags', {}).get('class', []))
        if ap_count == 0:
            weaknesses.append("Full AD comp (easy to itemize against)")
        elif ap_count >= 4:
            weaknesses.append("Full AP comp (vulnerable to MR stacking)")
        
        return weaknesses[:3]  # Top 3 weaknesses
    
    def _analyze_matchups(self, blue_picks: Dict, red_picks: Dict) -> List[Dict[str, Any]]:
        """Analyze lane matchups"""
        matchups = []
        roles = ['top', 'mid', 'adc']  # Focus on lane matchups
        
        for role in roles:
            if role in blue_picks and role in red_picks:
                blue_champ = blue_picks[role]
                red_champ = red_picks[role]
                
                matchup = self._evaluate_matchup(blue_champ, red_champ, role)
                matchups.append(matchup)
        
        return matchups
    
    def _evaluate_matchup(self, blue_champ: Dict, red_champ: Dict, role: str) -> Dict[str, Any]:
        """Evaluate individual lane matchup"""
        # Simple heuristic - in production you'd have a matchup database
        blue_skill = blue_champ.get('skill_cap', 1)
        red_skill = red_champ.get('skill_cap', 1)
        
        # Higher skill cap often means more outplay potential
        if blue_skill > red_skill:
            advantage = "blue"
            note = f"{blue_champ['name']} has higher skill ceiling"
        elif red_skill > blue_skill:
            advantage = "red"
            note = f"{red_champ['name']} has higher skill ceiling"
        else:
            advantage = "even"
            note = "Skill matchup"
        
        return {
            "lane": role.upper(),
            "blue_champion": blue_champ['name'],
            "red_champion": red_champ['name'],
            "advantage": advantage,
            "note": note,
            "tips": self._get_matchup_tips(blue_champ, red_champ, advantage)
        }
    
    def _get_matchup_tips(self, blue_champ: Dict, red_champ: Dict, advantage: str) -> List[str]:
        """Generate matchup-specific tips"""
        tips = []
        
        if advantage == "blue":
            tips.append(f"Play aggressive and pressure {red_champ['name']}")
            tips.append("Look for early leads to snowball")
        elif advantage == "red":
            tips.append(f"Play safe and farm under tower if needed")
            tips.append(f"Wait for jungle ganks to stabilize")
        else:
            tips.append("Focus on CS and trading evenly")
            tips.append("Look for jungle assistance to gain advantage")
        
        return tips[:2]
    
    def _get_win_conditions(self, own_comp: Dict, enemy_comp: Dict, team_side: str) -> List[str]:
        """Generate win conditions for a team"""
        conditions = []
        
        comp_type = own_comp.get('type', '')
        
        if "Teamfight" in comp_type:
            conditions.append("Force 5v5 teamfights around objectives")
            conditions.append("Group and use engage tools effectively")
        elif "Poke" in comp_type:
            conditions.append("Poke enemies before objectives")
            conditions.append("Avoid all-ins, kite and poke")
        elif "Split Push" in comp_type:
            conditions.append("Apply side lane pressure")
            conditions.append("Force enemy to respond to split pushers")
        
        # Add scaling condition if needed
        conditions.append("Control vision around objectives")
        
        return conditions[:3]
    
    def _identify_threats(self, own_picks: Dict, enemy_picks: Dict, team_side: str) -> List[Dict[str, str]]:
        """Identify key enemy threats"""
        threats = []
        
        for role, champ in enemy_picks.items():
            threat_level = self._assess_threat_level(champ, own_picks)
            if threat_level >= 2:  # Medium or High threat
                threats.append({
                    "champion": champ['name'],
                    "role": role.upper(),
                    "threat_level": "High" if threat_level >= 3 else "Medium",
                    "reason": self._get_threat_reason(champ)
                })
        
        # Sort by threat level and return top 3
        return sorted(threats, key=lambda x: 0 if x['threat_level'] == 'High' else 1)[:3]
    
    def _assess_threat_level(self, champ: Dict, own_picks: Dict) -> int:
        """Assess how threatening a champion is (0-3 scale)"""
        # Base threat on skill cap and damage potential
        skill_cap = champ.get('skill_cap', 1)
        
        # High skill cap champs are more threatening
        if skill_cap >= 3:
            return 3
        elif skill_cap >= 2:
            return 2
        else:
            return 1
    
    def _get_threat_reason(self, champ: Dict) -> str:
        """Get reason why champion is threatening"""
        classes = champ.get('tags', {}).get('class', [])
        
        if 'Assassin' in classes:
            return "High burst damage and mobility"
        elif 'Fighter' in classes:
            return "Strong dueling and sustained damage"
        elif 'Mage' in classes:
            return "High magic damage and CC"
        elif 'Marksman' in classes:
            return "High sustained DPS"
        elif 'Tank' in classes:
            return "Strong engage and peel"
        else:
            return "Versatile threat"
    
    def _analyze_power_spikes(self, picks: Dict) -> Dict[str, List[str]]:
        """Analyze when team hits power spikes"""
        spikes = {
            "early": [],
            "mid": [],
            "late": []
        }
        
        for role, champ in picks.items():
            champ_name = champ['name']
            
            # Simple heuristic - would use champion database in production
            if role in ['jgl', 'sup']:
                spikes['early'].append(f"{champ_name} (Level 3-6)")
            elif role in ['top', 'mid']:
                spikes['mid'].append(f"{champ_name} (Level 9-11, 2 items)")
            else:  # adc
                spikes['late'].append(f"{champ_name} (Level 13+, 3 items)")
        
        return spikes
    
    def _generate_game_plan(
        self, 
        blue_comp: Dict, 
        red_comp: Dict, 
        blue_win_prob: float,
        elo: str
    ) -> Dict[str, List[str]]:
        """Generate phase-by-phase game plan"""
        game_plan = {
            "early_game": [],
            "mid_game": [],
            "late_game": []
        }
        
        # Early game
        game_plan['early_game'].append("Focus on CS and vision control")
        if blue_comp.get('engage_potential') == "High":
            game_plan['early_game'].append("Look for early ganks and skirmishes")
        else:
            game_plan['early_game'].append("Play safe and scale")
        
        # Mid game
        game_plan['mid_game'].append("Group for objectives (Drake/Herald)")
        comp_type = blue_comp.get('type', '')
        if "Teamfight" in comp_type:
            game_plan['mid_game'].append("Force teamfights around objectives")
        else:
            game_plan['mid_game'].append("Apply map pressure and control vision")
        
        # Late game
        if blue_win_prob > 0.55:
            game_plan['late_game'].append("Push advantages and close out game")
        else:
            game_plan['late_game'].append("Play for picks and avoid risky fights")
        game_plan['late_game'].append("Secure Baron and Elder Drake for game-ending push")
        
        return game_plan


# Global instance
draft_analyzer = DraftAnalyzer()

