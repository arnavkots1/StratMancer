# StratMancer API Quick Start

## 🚀 Starting the API

### Option 1: Using the start script (Recommended)
```bash
python start_api.py
```

### Option 2: Using uvicorn directly
```bash
uvicorn backend.api.main:app --reload
```

The API will start at: **http://localhost:8000**

---

## 📚 Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/healthz

---

## 🔑 Authentication

Most endpoints require an API key in the header:
```
X-STRATMANCER-KEY: dev-key-change-in-production
```

---

## 📝 Example Request

### Predict Draft
```bash
curl -X POST http://localhost:8000/predict-draft \
  -H "X-STRATMANCER-KEY: dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "elo": "mid",
    "patch": "15.20",
    "blue": {
      "top": 266,
      "jgl": 64,
      "mid": 103,
      "adc": 51,
      "sup": 12,
      "bans": [53, 89, 412]
    },
    "red": {
      "top": 24,
      "jgl": 76,
      "mid": 238,
      "adc": 498,
      "sup": 267,
      "bans": [421, 75, 268]
    }
  }'
```

**Response:**
```json
{
  "blue_win_prob": 0.61,
  "red_win_prob": 0.39,
  "confidence": 0.82,
  "calibrated": true,
  "explanations": [
    "+Strong frontline/engage advantage",
    "-Low AP damage (predictable)",
    "+Early power spike"
  ],
  "model_version": "mid-xgb-20251017"
}
```

---

## 🧪 Testing

Run the test suite:
```bash
# Start the API first
python start_api.py

# Then in another terminal
python test_api.py
```

---

## 🔧 Configuration

Create a `.env` file or set environment variables:
```bash
STRATMANCER_API_KEY=your-secret-key-here
LOG_LEVEL=INFO
USE_REDIS=false
```

---

## 📊 Available Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/healthz` | GET | No | Health check |
| `/predict-draft` | POST | Yes | Predict draft outcome |
| `/models/registry` | GET | Yes | Get model metadata |
| `/team-optimizer/player/{puuid}` | GET | Yes | Get player metrics |
| `/meta/{elo}/{patch}` | GET | No | Get meta snapshot for a specific patch |
| `/meta/{elo}/latest` | GET | No | Get latest meta snapshot |
| `/meta/trends/{elo}` | GET | No | Get patch-over-patch risers and fallers |

---

## 🎯 Features

- ✅ **ELO-Specialized Models** - Separate models for low/mid/high ranks
- ✅ **Calibrated Predictions** - Isotonic regression for accurate probabilities
- ✅ **Smart Caching** - 60-second cache with Redis/memory fallback
- ✅ **Rate Limiting** - 60 requests/minute per IP
- ✅ **Meta Tracker** - Patch-aware pick/win/ban rates with Redis caching
- ✅ **CORS Enabled** - Ready for frontend integration
- ✅ **OpenAPI Docs** - Interactive API documentation
- ✅ **Error Handling** - Comprehensive error responses

---

## 📦 Requirements

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic-settings>=2.0.0
redis>=5.0.0  # Optional
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🔍 Troubleshooting

### Port already in use
```bash
# Kill existing process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Model not found errors
Train models first:
```bash
python ml_pipeline/models/train.py --model xgb --elo mid
```

### Import errors
Make sure you're in the project root and dependencies are installed:
```bash
pip install -r requirements.txt
```

---

**For detailed documentation, see `STEP3A_COMPLETE.md`**

