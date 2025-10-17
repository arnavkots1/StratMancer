"""
Inference service - loads models and makes predictions
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import numpy as np

# Add project root to path
sys.path.insert(0, '.')

from ml_pipeline.features import load_feature_map, assemble_features
from ml_pipeline.features.history_index import HistoryIndex
from ml_pipeline.models.predict import load_model as load_ml_model, predict_proba

from backend.config import settings

logger = logging.getLogger(__name__)


class InferenceService:
    """Service for model inference"""
    
    def __init__(self):
        self.feature_map: Optional[Dict] = None
        self.history_index: Optional[HistoryIndex] = None
        self.models: Dict[str, Tuple[Any, Any, Dict]] = {}  # elo -> (model, calibrator, modelcard)
        self._initialized = False
    
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
    
    def load_elo_model(self, elo: str) -> Tuple[Any, Any, Dict]:
        """Load model for specific ELO (lazy loading)"""
        if not self._initialized:
            self.initialize()
        
        if elo in self.models:
            return self.models[elo]
        
        logger.info(f"Loading model for {elo} ELO...")
        
        try:
            model, calibrator, modelcard = load_ml_model(
                elo_group=elo,
                model_dir=settings.MODEL_DIR
            )
            
            self.models[elo] = (model, calibrator, modelcard)
            logger.info(f"Model loaded for {elo}: {modelcard.get('model_type', 'unknown')}")
            
            return model, calibrator, modelcard
        
        except FileNotFoundError as e:
            logger.error(f"Model not found for {elo}: {e}")
            raise ValueError(f"No model available for ELO group: {elo}")
        except Exception as e:
            logger.error(f"Failed to load model for {elo}: {e}")
            raise
    
    def predict_draft(
        self,
        elo: str,
        patch: str,
        blue_picks: list,
        red_picks: list,
        blue_bans: list,
        red_bans: list
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
        model, calibrator, modelcard = self.load_elo_model(elo)
        model_type = modelcard.get('model_type', 'xgb')
        
        # Create match-like dictionary for feature assembly
        match_data = {
            'match_id': 'api_request',
            'patch': patch,
            'elo_rank': elo.upper(),
            'blue_picks': blue_picks,
            'red_picks': red_picks,
            'blue_bans': blue_bans + [-1] * (5 - len(blue_bans)),  # Pad to 5
            'red_bans': red_bans + [-1] * (5 - len(red_bans)),  # Pad to 5
            'blue_win': None,  # Unknown
            'champion_stats': [],  # Not needed for prediction
            'derived_features': {}  # Will be computed
        }
        
        # Assemble features
        try:
            X, named = assemble_features(
                match_data,
                elo.upper(),
                self.feature_map,
                self.history_index
            )
        except Exception as e:
            logger.error(f"Feature assembly failed: {e}")
            raise ValueError(f"Failed to assemble features: {str(e)}")
        
        # Get uncalibrated prediction
        y_pred_proba = predict_proba(model, X.reshape(1, -1), model_type)
        
        # Handle different return types
        if isinstance(y_pred_proba, np.ndarray):
            if y_pred_proba.ndim > 0:
                y_pred_proba = float(y_pred_proba[0]) if len(y_pred_proba) > 0 else float(y_pred_proba)
            else:
                y_pred_proba = float(y_pred_proba)
        
        # Apply calibration
        y_pred_calibrated = calibrator.predict(np.array([y_pred_proba]))[0]
        y_pred_calibrated = float(np.clip(y_pred_calibrated, 0.0, 1.0))
        
        # Calculate confidence (inverse entropy)
        probs = np.array([1 - y_pred_calibrated, y_pred_calibrated])
        probs = np.clip(probs, 1e-10, 1 - 1e-10)
        entropy = -np.sum(probs * np.log2(probs))
        confidence = float(1.0 - (entropy / 1.0))  # Normalize by max entropy
        
        # Generate simple explanations based on composition features
        explanations = self._generate_explanations(named, y_pred_calibrated)
        
        # Format response
        result = {
            'blue_win_prob': y_pred_calibrated,
            'red_win_prob': 1.0 - y_pred_calibrated,
            'confidence': confidence,
            'calibrated': True,
            'explanations': explanations,
            'model_version': f"{elo}-{model_type}-{modelcard.get('timestamp', 'unknown')[:8]}",
            'elo_group': elo,
            'patch': patch
        }
        
        return result
    
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

