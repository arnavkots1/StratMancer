"""
Configuration management for the application.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration from YAML and environment variables"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self._load_config()
        self._override_with_env()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def _override_with_env(self):
        """Override config values with environment variables"""
        # API key from environment takes precedence
        env_api_key = os.getenv('RIOT_API_KEY')
        if env_api_key:
            self.config['riot_api']['key'] = env_api_key
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'riot_api.key')
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Example:
            config.get('riot_api.key')
            config.get('collection.ranks')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_riot_api_key(self) -> str:
        """Get Riot API key"""
        key = self.get('riot_api.key')
        if not key or key == 'RGAPI-YOUR-API-KEY-HERE':
            raise ValueError(
                "Riot API key not configured. Please set RIOT_API_KEY in .env "
                "or update config/config.yaml"
            )
        return key
    
    def get_region(self) -> str:
        """Get default region"""
        return self.get('riot_api.region', 'na1')
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limit configuration"""
        return {
            'requests_per_second': self.get('riot_api.rate_limits.requests_per_second', 20),
            'requests_per_2_minutes': self.get('riot_api.rate_limits.requests_per_2_minutes', 100)
        }
    
    def get_ranks(self) -> list:
        """Get list of ranks to collect"""
        return self.get('collection.ranks', ['GOLD', 'PLATINUM', 'DIAMOND'])
    
    def get_queue_id(self) -> int:
        """Get queue ID (420 = Ranked Solo/Duo)"""
        return self.get('collection.queue_id', 420)
    
    def get_storage_path(self) -> Path:
        """Get base storage path"""
        return Path(self.get('storage.base_path', 'data'))
    
    def get_storage_formats(self) -> list:
        """Get enabled storage formats"""
        return self.get('storage.formats', ['parquet'])
    
    def should_save_raw(self) -> bool:
        """Check if raw API responses should be saved"""
        return self.get('collection.save_raw', False)


# Global config instance
_config_instance = None


def get_config(config_path: str = "config/config.yaml") -> ConfigManager:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigManager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance

