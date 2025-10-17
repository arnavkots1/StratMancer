"""
PUUID Cache for efficient summoner lookups.
Caches summoner ID -> PUUID mappings to avoid redundant API calls.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PUUIDCache:
    """Cache for summoner ID to PUUID mappings."""
    
    def __init__(self, cache_file: str = "data/puuid_cache.json", 
                 ttl_days: int = 7):
        """
        Initialize PUUID cache.
        
        Args:
            cache_file: Path to cache file
            ttl_days: Time-to-live for cache entries in days
        """
        self.cache_file = Path(cache_file)
        self.ttl_days = ttl_days
        self.cache: Dict[str, Dict] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} entries from PUUID cache")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            logger.info("No existing cache found, starting fresh")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug(f"Saved {len(self.cache)} entries to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get(self, summoner_id: str) -> Optional[str]:
        """
        Get PUUID for a summoner ID.
        
        Args:
            summoner_id: Summoner ID
            
        Returns:
            PUUID if found and not expired, None otherwise
        """
        if summoner_id not in self.cache:
            return None
        
        entry = self.cache[summoner_id]
        
        # Check if entry is expired
        cached_time = datetime.fromisoformat(entry['timestamp'])
        if datetime.now() - cached_time > timedelta(days=self.ttl_days):
            logger.debug(f"Cache entry for {summoner_id} expired")
            del self.cache[summoner_id]
            return None
        
        return entry['puuid']
    
    def set(self, summoner_id: str, puuid: str):
        """
        Cache a summoner ID -> PUUID mapping.
        
        Args:
            summoner_id: Summoner ID
            puuid: PUUID
        """
        self.cache[summoner_id] = {
            'puuid': puuid,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save every 50 entries to avoid losing too much progress
        if len(self.cache) % 50 == 0:
            self._save_cache()
    
    def save(self):
        """Explicitly save cache to disk."""
        self._save_cache()
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'total_entries': len(self.cache),
            'file_exists': self.cache_file.exists()
        }


