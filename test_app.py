"""
Minimal FastAPI app for Railway testing
"""
from fastapi import FastAPI
import os

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Hello World", "port": os.getenv("PORT", "8000")}

@app.get("/health")
@app.get("/healthz")
async def health():
    return {"status": "ok", "port": os.getenv("PORT", "8000")}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
