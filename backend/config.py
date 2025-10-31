"""
Configuration for StratMancer API
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API Configuration"""
    
    # API Settings
    APP_NAME: str = "StratMancer API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Authentication
    API_KEY: Optional[str] = os.getenv("STRATMANCER_API_KEY", "dev-key-change-in-production")
    
    # Gemini AI (for patch note featurization)
    GEMINI_API_KEY: Optional[str] = None
    
    # CORS - Security: Only allow specific origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://riftai.com",
        "https://riftai.vercel.app",
        "https://www.riftai.com",
    ]
    
    # Security Settings
    MAX_PAYLOAD_SIZE: int = int(os.getenv("MAX_PAYLOAD_SIZE", "32768"))  # 32KB
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "3"))  # 3 seconds
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    ENABLE_TRACING: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    
    # Logging Security
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    SANITIZE_LOGS: bool = True  # Remove sensitive data from logs
    
    # Redis (for cache and rate limiting)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = 0
    CACHE_TTL: int = 60  # seconds
    USE_REDIS: bool = os.getenv("USE_REDIS", "false").lower() == "true"
    
    # Model Paths
    MODEL_DIR: str = "ml_pipeline/models/trained"
    FEATURE_MAP_PATH: str = "ml_pipeline/feature_map.json"
    HISTORY_INDEX_PATH: str = "ml_pipeline/history_index.json"
    MODELCARDS_DIR: str = "ml_pipeline/models/modelcards"
    
    # Team Optimizer
    TEAM_OPTIMIZER_DATA_DIR: str = "ml_pipeline/team_optimizer"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting (Token Bucket with Redis)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_IP: int = 60        # requests per minute
    RATE_LIMIT_PER_KEY: int = 600      # requests per minute
    RATE_LIMIT_GLOBAL: int = 3000      # requests per minute
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()

