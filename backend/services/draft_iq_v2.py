"""
Draft IQ v2 - Professional coach-style draft analysis using Gemini AI.
Produces structured JSON and Markdown output with team overviews, lane analysis, and phase predictions.
"""

import logging
import json
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field

from backend.services.gemini_client import get_gemini_client, GeminiError
from backend.services.inference import inference_service
from ml_pipeline.features.feature_engineering import comp_shape_features
from ml_pipeline.features import load_feature_map

logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Schemas (Strict JSON Schema)
# ============================================================================

class RoleNote(BaseModel):
    role: Literal["Top", "Jungle", "Mid", "ADC", "Support"]
    champion: str
    notes: str


class TeamOverview(BaseModel):
    elo_context: Literal["High", "Mid", "Low"]
    items: List[RoleNote]
    identity: str


class LaneOutcome(BaseModel):
    lane: Literal["Top", "Jungle", "Mid", "Bot"]
    likely_winner: Literal[
        "Blue early", "Blue", "Even", "Red", "Red later",
        "Slight Blue early, Red later",
        "Skill-based, slightly Blue",
        "Skill-based, slightly Red"
    ]
    explanation: str


class FactorRow(BaseModel):
    factor: str
    blue: str
    red: str


class PhaseRow(BaseModel):
    phase: Literal["Early (0-10 min)", "Mid (10-25 min)", "Late (25+ min)"]
    favored: Literal["Blue", "Red", "Even", "Slight Blue", "Slight Red", "Red >> Blue", "Blue >> Red"]
    comment: str


class Probability(BaseModel):
    blue_range: str  # e.g. "25 – 30 %"
    red_range: str   # e.g. "70 – 75 %"


class DraftIQV2(BaseModel):
    elo_context: Literal["High", "Mid", "Low"]
    patch: str
    blue_overview: TeamOverview
    red_overview: TeamOverview
    lane_by_lane: List[LaneOutcome]
    teamfight_scaling_execution: List[FactorRow]
    phase_predictions: List[PhaseRow]
    final_prediction: Probability
    model_version: str
    calibration_note: str


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are StratMancer's Draft Analysis AI.

Input: Draft data with champion picks, bans, win probabilities, and composition metrics.

Your task: Analyze the draft and output JSON matching the required schema.

Output STRICT JSON:
{
  "elo_context": "High|Mid|Low",
  "patch": "string",
  "blue_overview": {
    "elo_context": "High|Mid|Low",
    "items": [{"role": "Top|Jungle|Mid|ADC|Support", "champion": "string", "notes": "string"}],
    "identity": "string"
  },
  "red_overview": { ... },
  "lane_by_lane": [{"lane": "Top|Jungle|Mid|Bot", "likely_winner": "string", "explanation": "string"}],
  "teamfight_scaling_execution": [{"factor": "string", "blue": "string", "red": "string"}],
  "phase_predictions": [{"phase": "Early (0-10 min)|Mid (10-25 min)|Late (25+ min)", "favored": "string", "comment": "string"}],
  "final_prediction": {"blue_range": "string", "red_range": "string"},
  "model_version": "string",
  "calibration_note": "string"
}

Use the provided data: win probabilities, champion names, composition metrics, and model version.
Keep explanations concise and professional."""


# ============================================================================
# Service Class
# ============================================================================

class DraftIQV2Service:
    """Service for generating Draft IQ v2 analysis"""
    
    def __init__(self):
        self.gemini = get_gemini_client()
        self.feature_map = None
        self._load_feature_map()
    
    def _load_feature_map(self):
        """Load feature map for champion names and tags"""
        try:
            self.feature_map = load_feature_map("ml_pipeline/feature_map.json")
            logger.info("Feature map loaded for Draft IQ v2")
        except Exception as e:
            logger.warning(f"Failed to load feature map: {e}")
            self.feature_map = {"champ_index": {}, "tags": {}}
    
    def _get_champion_name(self, champion_id: int) -> str:
        """Get champion name from ID"""
        if not self.feature_map:
            return f"Champion_{champion_id}"
        
        champ_index = self.feature_map.get("champ_index", {})
        for name, cid in champ_index.items():
            if cid == champion_id:
                return name
        
        return f"Champion_{champion_id}"
    
    def _assemble_draft_data(
        self,
        elo: str,
        patch: str,
        blue_picks: List[int],
        red_picks: List[int],
        blue_bans: List[int],
        red_bans: List[int],
        prediction_result: Dict[str, Any],
        named_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble factual data for LLM input"""
        
        # Get composition features
        comp_features = named_features.get("comp_features", {})
        
        # Build match dict for comp_shape_features
        match_dict = {
            "blue_picks": [cid for cid in blue_picks if cid >= 0],
            "red_picks": [cid for cid in red_picks if cid >= 0],
        }
        
        # Calculate additional comp features if not present
        if not comp_features and self.feature_map:
            try:
                comp_features = comp_shape_features(match_dict, self.feature_map)
            except Exception as e:
                logger.warning(f"Failed to compute comp features: {e}")
                comp_features = {}
        
        # Build user payload - use simple structure like patchnote_featurizer
        # Put champion names in a separate mapping, not in the main data
        role_order = ["Top", "Jungle", "Mid", "ADC", "Support"]
        
        # Champion name mapping (separate from main data to avoid triggering filters)
        champion_names = {}
        for champ_id in blue_picks + red_picks + blue_bans + red_bans:
            if champ_id >= 0:
                champion_names[str(champ_id)] = self._get_champion_name(champ_id)
        
        payload = {
            "elo": elo.capitalize(),
            "patch": patch,
            "blue_win_probability": round(prediction_result.get("blue_win_prob", 0.5), 3),
            "calibrated_blue_win_prob": round(prediction_result.get("blue_win_prob_calibrated", 0.5), 3),
            "confidence": round(prediction_result.get("confidence", 0.0), 3),
            "blue_team": {
                role_order[i]: blue_picks[i]
                for i in range(5) if blue_picks[i] >= 0
            },
            "red_team": {
                role_order[i]: red_picks[i]
                for i in range(5) if red_picks[i] >= 0
            },
            "blue_bans": [ban for ban in blue_bans if ban >= 0],
            "red_bans": [ban for ban in red_bans if ban >= 0],
            "champion_names": champion_names,
            "composition_metrics": {
                "blue_ap_ad_ratio": round(comp_features.get("blue_ap_ad_ratio", 0.5), 2),
                "red_ap_ad_ratio": round(comp_features.get("red_ap_ad_ratio", 0.5), 2),
                "engage_diff": round(comp_features.get("engage_diff", 0.0), 2),
                "cc_diff": round(comp_features.get("cc_diff", 0.0), 2),
                "poke_diff": round(comp_features.get("poke_diff", 0.0), 2),
                "frontline_diff": round(comp_features.get("frontline_diff", 0.0), 2),
                "early_diff": round(comp_features.get("early_diff", 0.0), 2),
                "mid_diff": round(comp_features.get("mid_diff", 0.0), 2),
                "late_diff": round(comp_features.get("late_diff", 0.0), 2),
            },
            "model_version": prediction_result.get("model_version", "unknown"),
        }
        
        return payload
    
    async def explain_draft_v2(
        self,
        elo: str,
        patch: str,
        blue_picks: List[int],
        red_picks: List[int],
        blue_bans: List[int],
        red_bans: List[int]
    ) -> DraftIQV2:
        """
        Generate Draft IQ v2 analysis.
        
        Args:
            elo: ELO group (low, mid, high)
            patch: Patch version
            blue_picks: List of 5 blue champion IDs
            red_picks: List of 5 red champion IDs
            blue_bans: List of blue ban IDs
            red_bans: List of red ban IDs
        
        Returns:
            DraftIQV2 model with analysis
        """
        # Get prediction first
        prediction_result = inference_service.predict_draft(
            elo=elo,
            patch=patch,
            blue_picks=blue_picks,
            red_picks=red_picks,
            blue_bans=blue_bans,
            red_bans=red_bans,
            calibrated_for_ui=True
        )
        
        # Get composition features by building match dict and computing
        named_features = {"comp_features": {}}
        try:
            # Create match dict for comp_shape_features
            match_data = {
                'blue_picks': [cid for cid in blue_picks if cid >= 0],
                'red_picks': [cid for cid in red_picks if cid >= 0],
            }
            
            # Compute comp features
            if self.feature_map:
                try:
                    comp_features = comp_shape_features(match_data, self.feature_map)
                    named_features = {"comp_features": comp_features}
                except Exception as e:
                    logger.warning(f"Failed to compute comp features: {e}")
        except Exception as e:
            logger.warning(f"Failed to get named features: {e}")
        
        # Assemble data for LLM
        user_payload = self._assemble_draft_data(
            elo, patch, blue_picks, red_picks, blue_bans, red_bans,
            prediction_result, named_features
        )
        
        # Try Gemini - NO FALLBACK, fail if Gemini doesn't work
        if not self.gemini.available():
            raise RuntimeError("Gemini client not available. Please set GEMINI_API_KEY environment variable.")
        
        logger.info("Calling Gemini for Draft IQ v2 analysis")
        llm_result = await self.gemini.complete_json(
            SYSTEM_PROMPT,
            user_payload,
            timeout_s=8,
            max_output_tokens=700
        )
        
        # Validate and return
        try:
            result = DraftIQV2(**llm_result)
            logger.info("Successfully generated Draft IQ v2 with Gemini")
            return result
        except Exception as e:
            logger.error(f"Gemini result failed validation: {e}")
            raise RuntimeError(f"Gemini returned invalid JSON structure: {e}. Response: {llm_result}")
    
    def _build_fallback_analysis(
        self,
        elo: str,
        patch: str,
        blue_picks: List[int],
        red_picks: List[int],
        blue_bans: List[int],
        red_bans: List[int],
        prediction_result: Dict[str, Any],
        named_features: Dict[str, Any]
    ) -> DraftIQV2:
        """Build deterministic fallback analysis"""
        
        elo_context_map = {"low": "Low", "mid": "Mid", "high": "High"}
        elo_context = elo_context_map.get(elo, "Mid")
        
        role_order = ["Top", "Jungle", "Mid", "ADC", "Support"]
        
        # Build team overviews
        blue_items = []
        red_items = []
        
        for i, role in enumerate(role_order):
            if i < len(blue_picks) and blue_picks[i] >= 0:
                champ_name = self._get_champion_name(blue_picks[i])
                tags = self.feature_map.get("tags", {}).get(str(blue_picks[i]), {})
                
                # Generate notes from tags
                notes_parts = []
                if tags.get("engage", 0) >= 2:
                    notes_parts.append("Strong engage")
                if tags.get("scaling_late", 0) >= 2:
                    notes_parts.append("Late scaling")
                if tags.get("scaling_early", 0) >= 2:
                    notes_parts.append("Early power")
                if not notes_parts:
                    notes_parts.append("Balanced pick")
                
                blue_items.append(RoleNote(
                    role=role,
                    champion=champ_name,
                    notes="; ".join(notes_parts[:2])
                ))
        
        for i, role in enumerate(role_order):
            if i < len(red_picks) and red_picks[i] >= 0:
                champ_name = self._get_champion_name(red_picks[i])
                tags = self.feature_map.get("tags", {}).get(str(red_picks[i]), {})
                
                notes_parts = []
                if tags.get("engage", 0) >= 2:
                    notes_parts.append("Strong engage")
                if tags.get("scaling_late", 0) >= 2:
                    notes_parts.append("Late scaling")
                if tags.get("scaling_early", 0) >= 2:
                    notes_parts.append("Early power")
                if not notes_parts:
                    notes_parts.append("Balanced pick")
                
                red_items.append(RoleNote(
                    role=role,
                    champion=champ_name,
                    notes="; ".join(notes_parts[:2])
                ))
        
        # Identity paragraphs - more detailed and coach-like
        comp_features = named_features.get("comp_features", {})
        blue_ap_ratio = comp_features.get("blue_ap_ad_ratio", 0.5)
        blue_engage = comp_features.get("blue_engage_score", 0.5)
        red_engage = comp_features.get("red_engage_score", 0.5)
        blue_poke = comp_features.get("blue_poke_score", 0.5)
        red_poke = comp_features.get("red_poke_score", 0.5)
        blue_scaling = comp_features.get("blue_scaling_score", 0.5)
        red_scaling = comp_features.get("red_scaling_score", 0.5)
        
        # Build blue identity
        blue_parts = []
        if blue_engage > 0.6:
            blue_parts.append("strong engage/initiation")
        if blue_poke > 0.6:
            blue_parts.append("poke-heavy")
        if blue_scaling > 0.6:
            blue_parts.append("late-game scaling")
        elif blue_scaling < 0.4:
            blue_parts.append("early game focused")
        
        ap_desc = "AP-heavy" if blue_ap_ratio > 0.7 else ("AD-heavy" if blue_ap_ratio < 0.3 else "balanced AP/AD")
        blue_parts.append(ap_desc)
        
        blue_identity = f"Team composition with {', '.join(blue_parts[:3])}."
        if blue_engage < 0.4:
            blue_identity += " Lacks hard engage; relies on picks or poke."
        if blue_scaling < 0.4:
            blue_identity += " Must win early or mid-game; weak late."
        
        # Build red identity
        red_parts = []
        if red_engage > 0.6:
            red_parts.append("strong engage/initiation")
        if red_poke > 0.6:
            red_parts.append("poke-heavy")
        if red_scaling > 0.6:
            red_parts.append("late-game scaling")
        elif red_scaling < 0.4:
            red_parts.append("early game focused")
        
        red_ap_ratio = comp_features.get("red_ap_ad_ratio", 0.5)
        red_ap_desc = "AP-heavy" if red_ap_ratio > 0.7 else ("AD-heavy" if red_ap_ratio < 0.3 else "balanced AP/AD")
        red_parts.append(red_ap_desc)
        
        red_identity = f"Team composition with {', '.join(red_parts[:3])}."
        if red_engage < 0.4:
            red_identity += " Lacks hard engage; relies on picks or poke."
        if red_scaling < 0.4:
            red_identity += " Must win early or mid-game; weak late."
        
        blue_overview = TeamOverview(
            elo_context=elo_context,
            items=blue_items,
            identity=blue_identity
        )
        red_overview = TeamOverview(
            elo_context=elo_context,
            items=red_items,
            identity=red_identity
        )
        
        # Lane-by-lane with detailed explanations based on champions and probabilities
        lane_by_lane = []
        blue_prob = prediction_result.get("blue_win_prob", 0.5)
        red_prob = 1.0 - blue_prob
        
        # Get champion names for each lane
        # Note: Bot lane uses ADC (index 3) and Support (index 4)
        lane_configs = [
            ("Top", 0, None),  # Top lane: Top role
            ("Jungle", 1, None),  # Jungle: Jungle role
            ("Mid", 2, None),  # Mid lane: Mid role
            ("Bot", 3, 4),  # Bot lane: ADC + Support
        ]
        
        for lane_name, primary_idx, secondary_idx in lane_configs:
            blue_primary_id = blue_picks[primary_idx] if primary_idx < len(blue_picks) else -1
            red_primary_id = red_picks[primary_idx] if primary_idx < len(red_picks) else -1
            
            # For bot lane, also get support
            blue_secondary_id = blue_picks[secondary_idx] if secondary_idx and secondary_idx < len(blue_picks) else -1
            red_secondary_id = red_picks[secondary_idx] if secondary_idx and secondary_idx < len(red_picks) else -1
            
            blue_primary_name = self._get_champion_name(blue_primary_id) if blue_primary_id >= 0 else "None"
            red_primary_name = self._get_champion_name(red_primary_id) if red_primary_id >= 0 else "None"
            blue_secondary_name = self._get_champion_name(blue_secondary_id) if blue_secondary_id >= 0 else None
            red_secondary_name = self._get_champion_name(red_secondary_id) if red_secondary_id >= 0 else None
            
            # Build matchup string
            if lane_name == "Bot" and blue_secondary_name and red_secondary_name:
                matchup_str = f"{blue_primary_name} + {blue_secondary_name} vs {red_primary_name} + {red_secondary_name}"
            else:
                matchup_str = f"{blue_primary_name} vs {red_primary_name}"
            
            # Get tags for both champions (average for bot lane)
            blue_tags = self.feature_map.get("tags", {}).get(str(blue_primary_id), {}) if blue_primary_id >= 0 else {}
            red_tags = self.feature_map.get("tags", {}).get(str(red_primary_id), {}) if red_primary_id >= 0 else {}
            
            # For bot lane, average with support for all attributes
            if lane_name == "Bot" and blue_secondary_id >= 0 and red_secondary_id >= 0:
                blue_sup_tags = self.feature_map.get("tags", {}).get(str(blue_secondary_id), {})
                red_sup_tags = self.feature_map.get("tags", {}).get(str(red_secondary_id), {})
                # Average all relevant attributes for bot lane
                blue_early = (blue_tags.get("scaling_early", 2) + blue_sup_tags.get("scaling_early", 2)) / 2
                blue_mid = (blue_tags.get("scaling_mid", 2) + blue_sup_tags.get("scaling_mid", 2)) / 2
                blue_late = (blue_tags.get("scaling_late", 2) + blue_sup_tags.get("scaling_late", 2)) / 2
                blue_engage = (blue_tags.get("engage", 0) + blue_sup_tags.get("engage", 0)) / 2
                blue_poke = (blue_tags.get("poke", 0) + blue_sup_tags.get("poke", 0)) / 2
                blue_cc = (blue_tags.get("hard_cc", 0) + blue_sup_tags.get("hard_cc", 0)) / 2
                red_early = (red_tags.get("scaling_early", 2) + red_sup_tags.get("scaling_early", 2)) / 2
                red_mid = (red_tags.get("scaling_mid", 2) + red_sup_tags.get("scaling_mid", 2)) / 2
                red_late = (red_tags.get("scaling_late", 2) + red_sup_tags.get("scaling_late", 2)) / 2
                red_engage = (red_tags.get("engage", 0) + red_sup_tags.get("engage", 0)) / 2
                red_poke = (red_tags.get("poke", 0) + red_sup_tags.get("poke", 0)) / 2
                red_cc = (red_tags.get("hard_cc", 0) + red_sup_tags.get("hard_cc", 0)) / 2
            else:
                blue_early = blue_tags.get("scaling_early", 2)
                blue_mid = blue_tags.get("scaling_mid", 2)
                blue_late = blue_tags.get("scaling_late", 2)
                blue_engage = blue_tags.get("engage", 0)
                blue_poke = blue_tags.get("poke", 0)
                blue_cc = blue_tags.get("hard_cc", 0)
                red_early = red_tags.get("scaling_early", 2)
                red_mid = red_tags.get("scaling_mid", 2)
                red_late = red_tags.get("scaling_late", 2)
                red_engage = red_tags.get("engage", 0)
                red_poke = red_tags.get("poke", 0)
                red_cc = red_tags.get("hard_cc", 0)
            
            # Calculate lane lean based on champion attributes and overall probability
            early_diff = blue_early - red_early
            mid_diff = blue_mid - red_mid
            late_diff = blue_late - red_late
            engage_diff = blue_engage - red_engage
            poke_diff = blue_poke - red_poke
            cc_diff = blue_cc - red_cc
            prob_diff = blue_prob - red_prob
            
            # Determine likely winner and explanation with more detail
            # Use more sensitive thresholds (0.5 instead of 1.0, 0.05 instead of 0.15)
            if blue_primary_id < 0 or red_primary_id < 0:
                likely_winner = "Even"
                explanation = f"{lane_name} lane not yet determined."
            elif prob_diff > 0.05:  # Blue slightly favored (5%+)
                if early_diff > 0.5:
                    likely_winner = "Blue early" if early_diff > 1.0 else "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Blue has stronger early game; can establish lane control and snowball."
                elif late_diff < -0.5:
                    likely_winner = "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Blue can pressure early, but Red scales better and outscales in extended trades."
                elif engage_diff > 0.5:
                    likely_winner = "Blue"
                    explanation = f"{matchup_str}: Blue has better engage and all-in potential; can force favorable trades."
                elif poke_diff > 0.5:
                    likely_winner = "Blue"
                    explanation = f"{matchup_str}: Blue has better poke and range control; can chip away and control lane."
                elif cc_diff > 0.5:
                    likely_winner = "Blue"
                    explanation = f"{matchup_str}: Blue has more crowd control; better setup for ganks and picks."
                elif late_diff > 0.5:
                    likely_winner = "Blue"
                    explanation = f"{matchup_str}: Blue scales better into late game; stronger teamfighting potential."
                else:
                    likely_winner = "Blue" if prob_diff > 0.08 else "Skill-based, slightly Blue"
                    explanation = f"{matchup_str}: Blue has slight advantage; better matchup, scaling, or utility."
            elif prob_diff < -0.05:  # Red slightly favored (5%+)
                if early_diff < -0.5:
                    likely_winner = "Red" if early_diff < -1.0 else "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Red dominates early and can snowball the lane advantage."
                elif late_diff > 0.5:
                    likely_winner = "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Blue can hold early, but Red scales harder and takes control post-6 or mid-game."
                elif engage_diff < -0.5:
                    likely_winner = "Red"
                    explanation = f"{matchup_str}: Red has better engage and all-in potential; can force favorable trades."
                elif poke_diff < -0.5:
                    likely_winner = "Red"
                    explanation = f"{matchup_str}: Red has better poke and range control; can chip away and control lane."
                elif cc_diff < -0.5:
                    likely_winner = "Red"
                    explanation = f"{matchup_str}: Red has more crowd control; better setup for ganks and picks."
                elif late_diff < -0.5:
                    likely_winner = "Red"
                    explanation = f"{matchup_str}: Red scales better into late game; stronger teamfighting potential."
                else:
                    likely_winner = "Red" if prob_diff < -0.08 else "Skill-based, slightly Red"
                    explanation = f"{matchup_str}: Red has slight advantage; better matchup, scaling, or utility."
            else:  # Very close matchup (within 5%)
                if early_diff > 0.5:
                    likely_winner = "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Blue has early pressure, but Red scales and contributes more in teamfights."
                elif early_diff < -0.5:
                    likely_winner = "Slight Blue early, Red later"
                    explanation = f"{matchup_str}: Red can pressure early, but Blue scales better and outscales later."
                elif engage_diff > 0.5:
                    likely_winner = "Skill-based, slightly Blue"
                    explanation = f"{matchup_str}: Blue has better engage tools; can win through all-in plays."
                elif engage_diff < -0.5:
                    likely_winner = "Skill-based, slightly Red"
                    explanation = f"{matchup_str}: Red has better engage tools; can win through all-in plays."
                elif poke_diff > 0.5:
                    likely_winner = "Skill-based, slightly Blue"
                    explanation = f"{matchup_str}: Blue has better poke and range advantage; can control lane through positioning."
                elif poke_diff < -0.5:
                    likely_winner = "Skill-based, slightly Red"
                    explanation = f"{matchup_str}: Red has better poke and range advantage; can control lane through positioning."
                elif cc_diff > 0.5:
                    likely_winner = "Skill-based, slightly Blue"
                    explanation = f"{matchup_str}: Blue has more CC tools; better setup for jungle ganks and picks."
                elif cc_diff < -0.5:
                    likely_winner = "Skill-based, slightly Red"
                    explanation = f"{matchup_str}: Red has more CC tools; better setup for jungle ganks and picks."
                else:
                    likely_winner = "Skill-based, slightly Blue" if prob_diff > 0 else "Skill-based, slightly Red"
                    explanation = f"{matchup_str}: Even matchup; outcome depends on player skill, jungle pressure, and wave management."
            
            lane_by_lane.append(LaneOutcome(
                lane=lane_name,
                likely_winner=likely_winner,
                explanation=explanation
            ))
        
        # Teamfight/Scaling/Execution factors
        factors = []
        
        engage_diff = comp_features.get("engage_diff", 0.0)
        if engage_diff > 0.1:
            factors.append(FactorRow(factor="Early skirmish", blue="Strong", red="Moderate"))
        elif engage_diff < -0.1:
            factors.append(FactorRow(factor="Early skirmish", blue="Moderate", red="Strong"))
        else:
            factors.append(FactorRow(factor="Early skirmish", blue="Moderate", red="Moderate"))
        
        late_diff = comp_features.get("late_diff", 0.0)
        if late_diff > 0.1:
            factors.append(FactorRow(factor="Scaling", blue="Better", red="Weaker"))
        elif late_diff < -0.1:
            factors.append(FactorRow(factor="Scaling", blue="Weaker", red="Better"))
        else:
            factors.append(FactorRow(factor="Scaling", blue="Even", red="Even"))
        
        blue_ap_ratio = comp_features.get("blue_ap_ad_ratio", 0.5)
        red_ap_ratio = comp_features.get("red_ap_ad_ratio", 0.5)
        ap_desc_blue = "Mixed" if 0.3 < blue_ap_ratio < 0.7 else ("AP-heavy" if blue_ap_ratio > 0.7 else "AD-heavy")
        ap_desc_red = "Mixed" if 0.3 < red_ap_ratio < 0.7 else ("AP-heavy" if red_ap_ratio > 0.7 else "AD-heavy")
        factors.append(FactorRow(factor="AP/AD mix", blue=ap_desc_blue, red=ap_desc_red))
        
        # Pick potential based on CC and engage
        blue_cc = sum(tags.get("hard_cc", 0) for tags in [self.feature_map.get("tags", {}).get(str(cid), {}) for cid in blue_picks if cid >= 0])
        red_cc = sum(tags.get("hard_cc", 0) for tags in [self.feature_map.get("tags", {}).get(str(cid), {}) for cid in red_picks if cid >= 0])
        
        if blue_cc > red_cc + 2:
            factors.append(FactorRow(factor="Pick potential", blue="Strong (multiple CC tools)", red="Moderate"))
        elif red_cc > blue_cc + 2:
            factors.append(FactorRow(factor="Pick potential", blue="Moderate", red="Strong (multiple CC tools)"))
        else:
            factors.append(FactorRow(factor="Pick potential", blue="Moderate", red="Moderate"))
        
        # Execution ease based on skill cap and coordination needs
        blue_skill_avg = sum(self.feature_map.get("tags", {}).get(str(cid), {}).get("skill_cap", 2) for cid in blue_picks if cid >= 0) / max(len([c for c in blue_picks if c >= 0]), 1)
        red_skill_avg = sum(self.feature_map.get("tags", {}).get(str(cid), {}).get("skill_cap", 2) for cid in red_picks if cid >= 0) / max(len([c for c in red_picks if c >= 0]), 1)
        
        if blue_skill_avg < 1.5:
            factors.append(FactorRow(factor="Execution ease", blue="Simple, straightforward", red="Requires coordination" if red_skill_avg > 2.5 else "Moderate"))
        elif red_skill_avg < 1.5:
            factors.append(FactorRow(factor="Execution ease", blue="Requires coordination" if blue_skill_avg > 2.5 else "Moderate", red="Simple, straightforward"))
        else:
            factors.append(FactorRow(factor="Execution ease", blue="Moderate", red="Moderate"))
        
        # Phase predictions
        early_diff = comp_features.get("early_diff", 0.0)
        mid_diff = comp_features.get("mid_diff", 0.0)
        late_diff = comp_features.get("late_diff", 0.0)
        
        phase_predictions = []
        
        # Phase predictions with detailed comments
        if early_diff > 0.15:
            phase_predictions.append(PhaseRow(
                phase="Early (0-10 min)",
                favored="Slight Blue",
                comment="Blue has stronger early game champions; can invade and secure early objectives."
            ))
        elif early_diff < -0.15:
            phase_predictions.append(PhaseRow(
                phase="Early (0-10 min)",
                favored="Slight Red",
                comment="Red has early power spikes; can pressure lanes and control jungle early."
            ))
        else:
            phase_predictions.append(PhaseRow(
                phase="Early (0-10 min)",
                favored="Even",
                comment="Even early game; outcome depends on jungle pathing and level 1 plays."
            ))
        
        if mid_diff > 0.15:
            phase_predictions.append(PhaseRow(
                phase="Mid (10-25 min)",
                favored="Blue",
                comment="Blue has mid-game power spikes; better teamfighting or objective control."
            ))
        elif mid_diff < -0.15:
            phase_predictions.append(PhaseRow(
                phase="Mid (10-25 min)",
                favored="Red",
                comment="Red mid-game advantage; picks start landing and teamfights favor Red."
            ))
        else:
            phase_predictions.append(PhaseRow(
                phase="Mid (10-25 min)",
                favored="Even",
                comment="Even mid game; both teams can contest objectives and fights."
            ))
        
        if late_diff > 0.15:
            phase_predictions.append(PhaseRow(
                phase="Late (25+ min)",
                favored="Blue",
                comment="Blue scales better; has stronger late-game teamfighting or wave control."
            ))
        elif late_diff < -0.15:
            phase_predictions.append(PhaseRow(
                phase="Late (25+ min)",
                favored="Red >> Blue",
                comment="Red significantly outscales; Blue lacks tools to contest late-game objectives."
            ))
        else:
            phase_predictions.append(PhaseRow(
                phase="Late (25+ min)",
                favored="Even",
                comment="Even late game; both teams can win through execution and positioning."
            ))
        
        # Final probabilities
        blue_prob = prediction_result.get("blue_win_prob", 0.5)
        red_prob = 1.0 - blue_prob
        
        # Format as ranges (center ± 3-5%)
        margin = 0.04
        blue_low = max(0, int((blue_prob - margin) * 100))
        blue_high = min(100, int((blue_prob + margin) * 100))
        red_low = max(0, int((red_prob - margin) * 100))
        red_high = min(100, int((red_prob + margin) * 100))
        
        final_prediction = Probability(
            blue_range=f"{blue_low} – {blue_high} %",
            red_range=f"{red_low} – {red_high} %"
        )
        
        return DraftIQV2(
            elo_context=elo_context,
            patch=patch,
            blue_overview=blue_overview,
            red_overview=red_overview,
            lane_by_lane=lane_by_lane,
            teamfight_scaling_execution=factors,
            phase_predictions=phase_predictions,
            final_prediction=final_prediction,
            model_version=prediction_result.get("model_version", "unknown"),
            calibration_note="Calibrated probabilities from ML model"
        )


# Global instance
_draft_iq_v2_service: Optional[DraftIQV2Service] = None


def get_draft_iq_v2_service() -> DraftIQV2Service:
    """Get or create global Draft IQ v2 service instance"""
    global _draft_iq_v2_service
    if _draft_iq_v2_service is None:
        _draft_iq_v2_service = DraftIQV2Service()
    return _draft_iq_v2_service


def to_markdown(iq: DraftIQV2) -> str:
    """Convert DraftIQV2 to Markdown format for copy/share"""
    lines = []
    
    # Header
    lines.append(f"# Draft IQ v2 Analysis — {iq.elo_context} ELO | Patch {iq.patch}\n")
    lines.append(f"Model: {iq.model_version}\n")
    lines.append(f"Note: {iq.calibration_note}\n")
    
    # Team Overviews
    lines.append(f"## 🔵 Blue Team ({iq.blue_overview.elo_context} ELO)\n")
    lines.append("| Role | Champion | Notes |")
    lines.append("|------|----------|-------|")
    for item in iq.blue_overview.items:
        lines.append(f"| {item.role} | {item.champion} | {item.notes} |")
    lines.append(f"\n**Identity:** {iq.blue_overview.identity}\n")
    
    lines.append(f"## 🔴 Red Team ({iq.red_overview.elo_context} ELO)\n")
    lines.append("| Role | Champion | Notes |")
    lines.append("|------|----------|-------|")
    for item in iq.red_overview.items:
        lines.append(f"| {item.role} | {item.champion} | {item.notes} |")
    lines.append(f"\n**Identity:** {iq.red_overview.identity}\n")
    
    # Lane-by-lane
    lines.append("## 🧩 Lane-by-Lane Analysis\n")
    lines.append("| Lane | Likely Winner | Explanation |")
    lines.append("|------|---------------|------------|")
    for lane in iq.lane_by_lane:
        lines.append(f"| {lane.lane} | {lane.likely_winner} | {lane.explanation} |")
    lines.append("")
    
    # Teamfight/Scaling/Execution
    lines.append("## ⚙️ Teamfighting / Scaling / Execution\n")
    lines.append("| Factor | Blue | Red |")
    lines.append("|--------|------|-----|")
    for factor in iq.teamfight_scaling_execution:
        lines.append(f"| {factor.factor} | {factor.blue} | {factor.red} |")
    lines.append("")
    
    # Phase Predictions
    lines.append("## 📊 Phase Predictions\n")
    lines.append("| Game Phase | Favored | Comment |")
    lines.append("|------------|---------|---------|")
    for phase in iq.phase_predictions:
        lines.append(f"| {phase.phase} | {phase.favored} | {phase.comment} |")
    lines.append("")
    
    # Final Prediction
    lines.append(f"## ✅ Realistic Win Probability ({iq.elo_context} ELO)\n")
    lines.append(f"Red ≈ {iq.final_prediction.red_range} | Blue ≈ {iq.final_prediction.blue_range}\n")
    
    return "\n".join(lines)

