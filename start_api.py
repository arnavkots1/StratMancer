"""
Start the StratMancer API server
"""

import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print("=" * 70)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 70)
    print(f"\n[*] API will be available at: http://localhost:8000")
    print(f"[*] API docs at: http://localhost:8000/docs")
    print(f"[*] Health check at: http://localhost:8000/healthz")
    print(f"\n[KEY] API Key: {settings.API_KEY}")
    print(f"      (Set in header: X-STRATMANCER-KEY)")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

