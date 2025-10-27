"""
Simplified FastAPI app for Railway deployment - FULL FUNCTIONALITY
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the FULL backend app
from backend.api.main import app

# The app from backend.api.main already has:
# - All ML routers (/predict-draft, /predict-meta, /recommend, /models)
# - All middleware (CORS, security, metrics)
# - All exception handlers
# - All functionality from start_api.py

logger.info(f"Loaded full StratMancer API v{settings.APP_VERSION}")
logger.info("All ML models and endpoints are available")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
