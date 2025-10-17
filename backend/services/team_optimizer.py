"""
Team optimizer service - computes team construction metrics
"""

import logging
import random
from pathlib import Path
from typing import Dict, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class TeamOptimizerService:
    """Service for team optimization metrics"""
    
    def __init__(self):
        self.data_dir = Path(settings.TEAM_OPTIMIZER_DATA_DIR)
        self._initialized = False
        self.player_data = {}  # puuid -> metrics (would be loaded from parquet/json)
    
    def initialize(self):
        """Initialize team optimizer data"""
        if self._initialized:
            return
        
        logger.info("Initializing team optimizer service...")
        
        # Check if data directory exists
        if not self.data_dir.exists():
            logger.warning(f"Team optimizer data directory not found: {self.data_dir}")
            logger.warning("Team optimizer will return mock data")
        else:
            # TODO: Load precomputed indices from parquet/json files
            # For now, this is a placeholder
            logger.info(f"Team optimizer data directory found: {self.data_dir}")
        
        self._initialized = True
        logger.info("Team optimizer service initialized")
    
    def get_player_metrics(self, puuid: str) -> Optional[Dict]:
        """
        Get team construction metrics for a player.
        
        For now, this returns None (404) as we don't have precomputed data yet.
        In production, this would load from parquet/json files.
        
        Args:
            puuid: Player PUUID
        
        Returns:
            Dictionary with metrics or None if not found
        """
        if not self._initialized:
            self.initialize()
        
        # Check if we have data for this player
        if puuid in self.player_data:
            return self.player_data[puuid]
        
        # TODO: Load from disk if not in memory
        
        # For now, return None (not found)
        return None
    
    def _generate_mock_metrics(self, puuid: str, elo: str = "mid") -> Dict:
        """
        Generate mock metrics for testing.
        This is for demonstration only - remove in production.
        """
        # Use PUUID as seed for consistent mock data
        random.seed(hash(puuid) % 2**32)
        
        return {
            "puuid": puuid,
            "elo": elo,
            "pick_equity": round(random.uniform(0.4, 0.9), 3),
            "economy_eff": round(random.uniform(0.5, 0.95), 3),
            "adaptability": round(random.uniform(0.3, 0.85), 3),
            "momentum": round(random.uniform(0.4, 0.9), 3),
            "macro_stability": round(random.uniform(0.5, 0.9), 3),
            "cohesion": round(random.uniform(0.6, 0.95), 3),
            "comfort": round(random.uniform(0.5, 0.95), 3),
            "tvs": round(random.uniform(0.45, 0.88), 3)
        }


# Global team optimizer service instance
team_optimizer_service = TeamOptimizerService()

