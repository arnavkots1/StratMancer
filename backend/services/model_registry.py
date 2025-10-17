"""
Model registry service - loads and manages model metadata
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from backend.config import settings

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages model metadata and versions"""
    
    def __init__(self):
        self.modelcards: Dict[str, dict] = {}
        self.feature_map_version: Optional[str] = None
        self.total_champions: int = 0
        self.last_updated: Optional[str] = None
        self._loaded = False
    
    def load_registry(self):
        """Load all model cards from disk"""
        if self._loaded:
            return
        
        logger.info("Loading model registry...")
        
        # Load feature map metadata
        feature_map_path = Path(settings.FEATURE_MAP_PATH)
        if feature_map_path.exists():
            try:
                with open(feature_map_path, 'r') as f:
                    feature_map = json.load(f)
                
                self.feature_map_version = feature_map['meta'].get('version', 'v1')
                self.total_champions = feature_map['meta']['num_champ']
                logger.info(f"Feature map loaded: {self.total_champions} champions, version {self.feature_map_version}")
            except Exception as e:
                logger.error(f"Failed to load feature map: {e}")
        
        # Load model cards
        modelcards_dir = Path(settings.MODELCARDS_DIR)
        if not modelcards_dir.exists():
            logger.warning(f"Model cards directory not found: {modelcards_dir}")
            self._loaded = True
            return
        
        # Find latest model card for each ELO
        elo_groups = ['low', 'mid', 'high']
        
        for elo in elo_groups:
            # Find all modelcards for this ELO
            modelcard_files = list(modelcards_dir.glob(f"modelcard_{elo}_*.json"))
            
            if not modelcard_files:
                logger.warning(f"No model cards found for {elo} ELO")
                continue
            
            # Get the latest one (by filename timestamp)
            latest_file = sorted(modelcard_files)[-1]
            
            try:
                with open(latest_file, 'r') as f:
                    modelcard = json.load(f)
                
                self.modelcards[elo] = modelcard
                logger.info(f"Loaded model card for {elo}: {modelcard.get('model_type', 'unknown')} @ {modelcard.get('timestamp', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to load model card {latest_file}: {e}")
        
        self.last_updated = datetime.now().isoformat()
        self._loaded = True
        
        logger.info(f"Model registry loaded: {len(self.modelcards)} ELO groups")
    
    def get_modelcard(self, elo: str) -> Optional[dict]:
        """Get model card for specific ELO"""
        if not self._loaded:
            self.load_registry()
        
        return self.modelcards.get(elo)
    
    def get_all_modelcards(self) -> Dict[str, dict]:
        """Get all model cards"""
        if not self._loaded:
            self.load_registry()
        
        return self.modelcards
    
    def get_feature_map_version(self) -> str:
        """Get feature map version"""
        if not self._loaded:
            self.load_registry()
        
        return self.feature_map_version or "unknown"
    
    def get_total_champions(self) -> int:
        """Get total number of champions"""
        if not self._loaded:
            self.load_registry()
        
        return self.total_champions
    
    def get_last_updated(self) -> str:
        """Get last update timestamp"""
        if not self._loaded:
            self.load_registry()
        
        return self.last_updated or datetime.now().isoformat()
    
    def reload(self):
        """Force reload of registry"""
        self._loaded = False
        self.modelcards.clear()
        self.load_registry()


# Global registry instance
model_registry = ModelRegistry()

