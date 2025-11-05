"""
Inference service - loads models and makes predictions
"""

import logging
import sys
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import numpy as np

# Add project root to path
sys.path.insert(0, '.')

from ml_pipeline.features import (
    load_feature_map,
    assemble_features,
    FeatureContext,
    FeatureFlags,
)
from ml_pipeline.features.history_index import HistoryIndex
from ml_pipeline.models.predict import load_model as load_ml_model, predict_raw_and_calibrated

from backend.config import settings

logger = logging.getLogger(__name__)


class InferenceService:
    """Service for model inference"""
    
    def __init__(self):
        self.feature_map: Optional[Dict] = None
        self.history_index: Optional[HistoryIndex] = None
        self.models: Dict[str, Tuple[Any, Any, str, Dict]] = {}  # elo -> (model, calibrator, method, modelcard)
        self._initialized = False
        self._feature_contexts: Dict[str, FeatureContext] = {}
    
    def clear_cache(self):
        """Clear loaded models to force reload."""
        self.models.clear()
        self._initialized = False
        logger.info("Inference service cache cleared - models will reload on next request")
    
    def initialize(self):
        """Lazy initialization of models and resources"""
        if self._initialized:
            return
        
        logger.info("Initializing inference service...")
        
        # Load feature map
        try:
            feature_map_path = Path(settings.FEATURE_MAP_PATH)
            if not feature_map_path.exists():
                raise FileNotFoundError(f"Feature map not found: {feature_map_path}")
            
            self.feature_map = load_feature_map(str(feature_map_path))
            logger.info(f"Feature map loaded: {self.feature_map['meta']['num_champ']} champions")
        except Exception as e:
            logger.error(f"Failed to load feature map: {e}")
            raise
        
        # Load history index
        try:
            history_index_path = Path(settings.HISTORY_INDEX_PATH)
            if history_index_path.exists():
                self.history_index = HistoryIndex()
                self.history_index.load(str(history_index_path))
                stats = self.history_index.get_stats()
                logger.info(f"History index loaded: {stats['total_matches']} matches")
            else:
                logger.warning(f"History index not found: {history_index_path}")
                self.history_index = None
        except Exception as e:
            logger.warning(f"Failed to load history index: {e}")
            self.history_index = None
        
        self._initialized = True
        logger.info("Inference service initialized")
    
    def load_elo_model(self, elo: str) -> Tuple[Any, Any, str, Dict]:
        """Load model for specific ELO (lazy loading)"""
        if not self._initialized:
            self.initialize()

        if elo in self.models:
            return self.models[elo]
        
        logger.info(f"Loading model for {elo} ELO...")
        
        try:
            # Load latest model (cache cleared on server restart or manual reload)
            model, calibrator, calibrator_method, modelcard = load_ml_model(
                elo_group=elo,
                model_dir=settings.MODEL_DIR
            )
            self._ensure_feature_context(elo, modelcard)
            
            self.models[elo] = (model, calibrator, calibrator_method, modelcard)
            logger.info(f"Model loaded for {elo}: {modelcard.get('model_type', 'unknown')}")
            logger.info(f"Model card features: {modelcard.get('features')}, mode: {modelcard.get('feature_mode')}")
            logger.info(f"Model card flags: {modelcard.get('feature_flags')}")
            
            return model, calibrator, calibrator_method, modelcard
        
        except FileNotFoundError as e:
            logger.error(f"Model not found for {elo}: {e}")
            raise ValueError(f"No model available for ELO group: {elo}")
        except Exception as e:
            logger.error(f"Failed to load model for {elo}: {e}")
            raise

    def _ensure_feature_context(self, elo: str, modelcard: Dict, force_rebuild: bool = False) -> FeatureContext:
        """Create or update feature context for an ELO based on model metadata.
        
        Args:
            elo: ELO group (low, mid, high)
            modelcard: Model metadata dictionary
            force_rebuild: If True, always rebuild context even if cached
        """
        if not self.feature_map:
            raise RuntimeError("Feature map must be loaded before building feature context.")

        model_feature_mode = modelcard.get('feature_mode', 'basic')
        flags_dict = modelcard.get('feature_flags', {})
        assets_dir = modelcard.get('assets_dir') or 'data/assets'

        # Check if we should rebuild (force_rebuild or context doesn't exist)
        context = self._feature_contexts.get(elo)
        should_rebuild = force_rebuild or context is None or context.mode != model_feature_mode
        
        if should_rebuild:
            logger.info(f"{'Force ' if force_rebuild else ''}Rebuilding feature context for {elo}: mode={model_feature_mode}, flags={flags_dict}")
            
            default_flags = FeatureFlags()
            default_flag_values = {field.name: getattr(default_flags, field.name) for field in dataclass_fields(FeatureFlags)}
            flag_kwargs = {
                name: bool(flags_dict.get(name, default_flag_values[name]))
                for name in default_flag_values
            }
            flags = FeatureFlags(**flag_kwargs)

            context = FeatureContext(
                feature_map=self.feature_map,
                mode=model_feature_mode,
                elo_group=elo,
                assets_dir=assets_dir,
                flags=flags,
            )
            embedding_dim_hint = modelcard.get('embedding_dim')
            if embedding_dim_hint is not None:
                context.embedding_dim_hint = int(embedding_dim_hint)
            
            self._feature_contexts[elo] = context
            logger.info(f"✅ Feature context ready for {elo}: mode={context.mode}, {len(context.flags.__dict__)} flags set")

        return context

    def _get_feature_context(self, elo: str) -> Optional[FeatureContext]:
        return self._feature_contexts.get(elo)
    
    def clear_context_cache(self, elo: Optional[str] = None):
        """Clear cached feature contexts to force rebuild.
        
        Args:
            elo: If provided, clear only this ELO's context. Otherwise clear all.
        """
        if elo:
            if elo in self._feature_contexts:
                logger.info(f"🗑️ Clearing cached context for {elo}")
                del self._feature_contexts[elo]
        else:
            logger.info(f"🗑️ Clearing all cached contexts ({len(self._feature_contexts)} entries)")
            self._feature_contexts.clear()
    
    def predict_draft(
        self,
        elo: str,
        patch: str,
        blue_picks: list,
        red_picks: list,
        blue_bans: list,
        red_bans: list,
        calibrated_for_ui: bool = True,
    ) -> Dict[str, Any]:
        """
        Make draft prediction.
        
        Args:
            elo: ELO group ('low', 'mid', 'high')
            patch: Patch version
            blue_picks: List of 5 blue champion IDs [top, jgl, mid, adc, sup]
            red_picks: List of 5 red champion IDs [top, jgl, mid, adc, sup]
            blue_bans: List of up to 5 blue ban IDs
            red_bans: List of up to 5 red ban IDs
        
        Returns:
            Prediction dictionary with probabilities and explanations
        """
        if not self._initialized:
            self.initialize()
        
        # Load model for this ELO
        model, calibrator, calibrator_method, modelcard = self.load_elo_model(elo)
        model_type = modelcard.get('model_type', 'xgb')
        
        # Ensure feature context is created with correct model card metadata
        context = self._ensure_feature_context(elo, modelcard)
        
        # Create match-like dictionary for feature assembly
        # Convert positional arrays to champion ID lists (same format as training data)
        def _normalize_pick(value: Any) -> int:
            if value is None:
                return -1
            try:
                return int(value)
            except (TypeError, ValueError):
                return -1

        blue_pick_list = [_normalize_pick(champ_id) for champ_id in blue_picks]
        red_pick_list = [_normalize_pick(champ_id) for champ_id in red_picks]
        if len(blue_pick_list) < 5:
            blue_pick_list.extend([-1] * (5 - len(blue_pick_list)))
        if len(red_pick_list) < 5:
            red_pick_list.extend([-1] * (5 - len(red_pick_list)))
        
        blue_bans_norm = [_normalize_pick(ban) for ban in blue_bans]
        red_bans_norm = [_normalize_pick(ban) for ban in red_bans]

        match_data = {
            'match_id': 'api_request',
            'patch': patch,
            'elo_rank': elo.upper(),
            'blue_picks': blue_pick_list,  # Use champion ID list, not positional array
            'red_picks': red_pick_list,    # Use champion ID list, not positional array
            'blue_bans': blue_bans_norm + [-1] * (5 - len(blue_bans_norm)),  # Pad to 5
            'red_bans': red_bans_norm + [-1] * (5 - len(red_bans_norm)),  # Pad to 5
            'blue_win': None,  # Unknown
            'champion_stats': [],  # Not needed for prediction
            'derived_features': {}  # Will be computed
        }
        
        # Assemble features - FIX CONTEXT CREATION
        try:
            # Create a proper feature context that matches the model's training
            if context is None:
                # Fallback: create context manually to match model card
                feature_flags = FeatureFlags(
                    use_embeddings=True,
                    use_matchups=True, 
                    use_synergy=True,
                    ban_context=True,
                    pick_order=False
                )
                context = FeatureContext(
                    feature_map=self.feature_map,
                    mode="rich",
                    elo_group=elo,
                    assets_dir="data/assets",
                    flags=feature_flags
                )
                logger.info(f"Created fallback context: mode={context.mode}, flags={context.flags.__dict__}")
            
            X, named = assemble_features(
                match_data,
                elo.upper(),
                self.feature_map,
                self.history_index,
                context=context
            )
            logger.info(f"Feature vector shape: {X.shape}, expected: 3410, blue_picks: {blue_pick_list}, red_picks: {red_pick_list}")
        except Exception as e:
            logger.error(f"Feature assembly failed: {e}")
            raise ValueError(f"Failed to assemble features: {str(e)}")
        
        # Get uncalibrated prediction
        raw_prob, calibrated_prob = predict_raw_and_calibrated(
            model,
            calibrator,
            calibrator_method,
            X.reshape(1, -1),
            model_type,
        )
        raw_prob = float(np.clip(raw_prob[0], 0.0, 1.0))
        calibrated_prob = float(np.clip(calibrated_prob[0], 0.0, 1.0))
        
        # DEBUG: Log the raw model output to understand what's happening
        logger.info(f"MODEL DEBUG: Raw prob={raw_prob:.6f}, Calibrated prob={calibrated_prob:.6f}, Model type={model_type}")

        filled_slots = sum(1 for cid in blue_pick_list if cid not in (-1, None)) + \
                       sum(1 for cid in red_pick_list if cid not in (-1, None))
        
        # REMOVED SHRINK FUNCTION - Models are trained with 60% blue bias
        # The shrink was neutralizing the blue bias by pulling predictions toward 50%
        # We want to preserve the model's blue bias predictions
        
        # Only apply minimal safety caps for incomplete drafts to prevent extreme predictions
        # Complete drafts (10 slots) use model predictions directly
        if filled_slots < 8:
            # Incomplete drafts: apply conservative caps to prevent extreme predictions
            raw_prob = max(0.25, min(0.75, raw_prob))
            calibrated_prob = max(0.25, min(0.75, calibrated_prob))
        
        selected_prob = calibrated_prob if calibrated_for_ui else raw_prob
        
        logger.debug(
            "Raw: %.4f, Calibrated: %.4f, Selected: %.4f, Filled slots: %d",
            raw_prob,
            calibrated_prob,
            selected_prob,
            filled_slots,
        )
        
        # Calculate confidence using standard formula: |p - 0.5| * 200
        # This gives 0% for 50/50 and 100% for 100/0 or 0/100
        # Using 200 multiplier to get full 0-100% range (original formula with * 100 gave 0-50%)
        # 
        # NOTE: Low confidence (5-15%) is expected when predictions are close to 50/50.
        # This indicates the model sees the draft as relatively balanced/uncertain, which is correct behavior.
        # Higher confidence would only occur if the model strongly favors one side (e.g., 60%+ or 40%-).
        confidence = float(abs(selected_prob - 0.5) * 200)
        
        # For complete drafts, boost confidence slightly to reflect model certainty
        if filled_slots >= 10:  # Complete draft
            confidence = min(confidence * 1.2, 100.0)  # 20% boost, cap at 100%
        
        # CRITICAL: Clamp confidence to 0-100 range to prevent any overflow or display bugs
        confidence = max(0.0, min(100.0, float(confidence)))
        
        # DEBUG: Log confidence calculation details
        logger.info(f"CONFIDENCE DEBUG: selected_prob={selected_prob:.4f}, confidence={confidence:.2f}%")
        logger.info(f"CONFIDENCE DEBUG: filled_slots={filled_slots}, complete_draft_boost={filled_slots >= 10}")
        if confidence < 15:
            logger.info(f"CONFIDENCE DEBUG: Low confidence due to near-neutral prediction (close to 50/50). This is expected for balanced drafts.")
        
        # Generate simple explanations based on composition features
        explanations = self._generate_explanations(named, selected_prob)
        
        # Format response
        result = {
            'blue_win_prob': selected_prob,
            'red_win_prob': 1.0 - selected_prob,
            'confidence': confidence,
            'calibrated': calibrated_for_ui,
            'probability_source': 'calibrated' if calibrated_for_ui else 'raw',
            'explanations': explanations,
            'model_version': f"{elo}-{model_type}-{modelcard.get('timestamp', 'unknown')[:8]}",
            'elo_group': elo,
            'patch': patch,
            'blue_win_prob_raw': raw_prob,
            'blue_win_prob_calibrated': calibrated_prob,
            'calibration_method': calibrator_method,
            'feature_context': {
                'mode': context.mode if context else 'basic',
                'flags': context.flags.__dict__ if context else {},
                'filled_slots': filled_slots,
            },
        }
        
        return result
    
    def predict_draft_with_roles(
        self,
        elo: str,
        patch: str,
        blue_draft: Dict,
        red_draft: Dict,
        calibrated_for_ui: bool = True,
    ) -> Dict[str, Any]:
        """
        Make draft prediction with role-aware champion placement.
        
        Args:
            elo: ELO group ('low', 'mid', 'high')
            patch: Patch version
            blue_draft: Dict with role -> champion_id mapping (or None/-1 for empty)
            red_draft: Dict with role -> champion_id mapping (or None/-1 for empty)
        
        Returns:
            Prediction dictionary with probabilities and explanations
        """
        # Convert role-based draft to positional arrays
        role_order = ['top', 'jgl', 'mid', 'adc', 'sup']
        
        blue_picks = []
        red_picks = []
        
        for role in role_order:
            blue_champ = blue_draft.get(role)
            red_champ = red_draft.get(role)
            
            # Convert None to -1, keep existing values
            blue_picks.append(blue_champ if blue_champ is not None else -1)
            red_picks.append(red_champ if red_champ is not None else -1)
        
        # Use the existing predict_draft method with positional arrays
        return self.predict_draft(
            elo=elo,
            patch=patch,
            blue_picks=blue_picks,
            red_picks=red_picks,
            blue_bans=blue_draft.get('bans', []),
            red_bans=red_draft.get('bans', []),
            calibrated_for_ui=calibrated_for_ui,
        )
    
    def _generate_explanations(self, named_features: Dict, blue_win_prob: float) -> list:
        """Generate human-readable explanations from features"""
        explanations = []
        
        comp_features = named_features.get('comp_features', {})
        
        # Engagement advantage
        engage_diff = comp_features.get('engage_diff', 0)
        if engage_diff > 0.2:
            explanations.append("+Strong frontline/engage advantage")
        elif engage_diff < -0.2:
            explanations.append("-Weak frontline/engage")
        
        # Damage composition
        blue_ap_ratio = comp_features.get('blue_ap_ad_ratio', 0.5)
        if blue_ap_ratio < 0.3:
            explanations.append("-Low AP damage (predictable)")
        elif blue_ap_ratio > 0.7:
            explanations.append("+High AP damage (diverse threats)")
        
        # Scaling
        early_diff = comp_features.get('early_diff', 0)
        late_diff = comp_features.get('late_diff', 0)
        
        if early_diff > 0.2:
            explanations.append("+Early power spike")
        elif late_diff > 0.2:
            explanations.append("+Late game scaling")
        
        # CC advantage
        cc_diff = comp_features.get('cc_diff', 0)
        if cc_diff > 0.2:
            explanations.append("+Superior crowd control")
        elif cc_diff < -0.2:
            explanations.append("-Lacks crowd control")
        
        # Poke composition
        poke_diff = comp_features.get('poke_diff', 0)
        if poke_diff > 0.2:
            explanations.append("+Strong poke/harass")
        
        # If no specific explanations, add generic one
        if not explanations:
            if blue_win_prob > 0.55:
                explanations.append("+Balanced composition")
            elif blue_win_prob < 0.45:
                explanations.append("-Team composition disadvantage")
            else:
                explanations.append("≈Even match expected")
        
        return explanations[:5]  # Max 5 explanations
    
    def get_models_status(self) -> Dict[str, bool]:
        """Get status of loaded models"""
        return {
            elo: elo in self.models
            for elo in ['low', 'mid', 'high']
        }


# Global inference service instance
inference_service = InferenceService()

