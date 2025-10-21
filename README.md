# StratMancer - League of Legends ML Platform

A production-ready data collection and ML platform for League of Legends match analysis.

🎯 **Step 1 Complete**: Data collection and schema foundation ready!

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your Riot API key

# 3. Check setup
python check_status.py

# 4. Test collection (10 matches)
python quickstart.py

# 5. Full collection (100+ matches per rank)
python run_collector.py --ranks GOLD PLATINUM DIAMOND --matches-per-rank 100
```

📖 **New here?** Start with [GET_STARTED.md](GET_STARTED.md)

## Features

- ✅ **Modular Architecture**: Clean separation of concerns, easy to extend
- ✅ **Riot API Integration**: Full-featured client with rate limiting
- ✅ **Automatic Patch Tagging**: Tracks game versions automatically
- ✅ **Elo Filtering**: Collect from Iron to Challenger
- ✅ **Multi-Format Storage**: Parquet (ML-ready) and JSON (human-readable)
- ✅ **Schema Validation**: Pydantic models ensure data integrity
- ✅ **Error Recovery**: Exponential backoff, automatic retries
- ✅ **Production Ready**: Logging, config management, unit tests
- ✅ **Docker Support**: Containerized deployment with docker-compose
- ✅ **Monitoring**: Prometheus metrics and OpenTelemetry tracing
- ✅ **Security**: Request validation, rate limiting, payload size limits
- ✅ **Testing**: Comprehensive API test suite with pytest

## Project Structure

```
StratMancer/
├── src/                    # Source code
│   ├── collectors/         # Match data collection
│   ├── transformers/       # Schema & data transformation
│   ├── storage/            # Storage handlers (Parquet/JSON)
│   └── utils/              # API client, rate limiter, config
├── config/                 # Configuration
│   └── config.yaml         # API keys and settings
├── data/                   # Collected data (auto-created)
│   ├── raw/               # Raw API responses
│   └── processed/         # Processed matches
├── notebooks/              # Jupyter notebooks
│   └── validation.ipynb   # Data validation
├── tests/                  # Unit tests
└── Documentation:
    ├── GET_STARTED.md      # Quick start guide
    ├── SETUP_GUIDE.md      # Detailed setup
    ├── ARCHITECTURE.md     # Technical details
    └── PROJECT_SUMMARY.md  # Complete summary
```

## Data Schema

Every match includes:

```python
MatchData:
  - match_id: str               # Unique match identifier
  - patch: str                  # Game version (e.g., "14.1")
  - elo_rank: str              # IRON → CHALLENGER
  - blue_picks: List[int]      # 5 champion IDs
  - red_picks: List[int]       # 5 champion IDs
  - blue_bans: List[int]       # 5 champion IDs
  - red_bans: List[int]        # 5 champion IDs
  - blue_win: bool             # True if blue team won
  - champion_stats: List[ChampionStats]  # 10 champions
      ├── id, role, kda, cs
      └── dmg_share, gold_share
  - objectives: Objectives
      └── dragons, heralds, barons, towers
  - derived_features: DerivedFeatures
      └── ap_ad_ratio, engage_score, splitpush_score, synergy
```

See `src/transformers/schema.py` for complete specification.

## Usage Examples

### Collect Data

```bash
# Test with 10 matches
python quickstart.py

# Collect 100 matches for specific ranks
python run_collector.py --ranks GOLD PLATINUM DIAMOND --matches-per-rank 100

# Collect all ranks
python run_collector.py --matches-per-rank 500

# Different region
python run_collector.py --region euw1 --matches-per-rank 100
```

### Load Data in Python

```python
from src.storage.data_storage import DataStorage

# Initialize storage
storage = DataStorage(base_path='data')

# Load matches
gold_matches = storage.load_matches('GOLD', format='parquet')

# Access match data
for match in gold_matches:
    print(f"Match {match.match_id}: Patch {match.patch}")
    print(f"  Blue win: {match.blue_win}")
    print(f"  Blue picks: {match.blue_picks}")
    print(f"  AP/AD ratio: {match.derived_features.ap_ad_ratio}")
```

### Validate Data

```bash
# Run validation notebook
jupyter notebook notebooks/validation.ipynb

# Or check status
python check_status.py
```

### Build Rich Feature Assets

```bash
# Generate matchup, priors, and embedding assets for a patch
python -m ml_pipeline.features.build_assets --elo mid --patch 14.21 --embedding-dim 32
```

### Train Rich Models

```bash
# Low / Mid / High elo groups with rich feature flags
python -m ml_pipeline.models.train --elo low  --features rich --use-embeddings --use-matchups --use-synergy --ban-context
python -m ml_pipeline.models.train --elo mid  --features rich --use-embeddings --use-matchups --use-synergy --ban-context
python -m ml_pipeline.models.train --elo high --features rich --use-embeddings --use-matchups --use-synergy --ban-context
```

### Evaluate & Gate Models

```bash
# Evaluate a trained model (writes metrics + reliability plots + gate result)
python -m ml_pipeline.models.evaluate \
  --elo mid \
  --model-type xgb \
  --model-path ml_pipeline/models/trained/draft_mid_xgb_<TIMESTAMP>.pkl \
  --calibrator-path ml_pipeline/models/trained/calibrator_mid_<TIMESTAMP>.pkl \
  --test-data data/processed/eval_mid.npz
```

## Configuration

Edit `config/config.yaml`:

```yaml
riot_api:
  key: "RGAPI-YOUR-KEY"      # Or use .env
  region: "na1"              # na1, euw1, kr, etc.
  rate_limits:
    requests_per_second: 20
    requests_per_2_minutes: 100

collection:
  ranks: ["GOLD", "PLATINUM", "DIAMOND"]
  queue_id: 420              # Ranked Solo/Duo
  matches_per_rank: 1000

storage:
  formats: ["parquet", "json"]
```

## Performance

- **Collection Speed**: ~1,500-2,000 matches/hour
- **Storage Efficiency**: 5-10 MB per 1,000 matches (Parquet)
- **Memory Usage**: Minimal (incremental saving)
- **Error Recovery**: Automatic retry with exponential backoff

## Documentation

- 🚀 **[GET_STARTED.md](GET_STARTED.md)** - Quick start in 5 minutes
- 📖 **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup and troubleshooting
- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture
- 📋 **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete feature list

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Check project status
python check_status.py

# Quick test collection
python quickstart.py
```

## Next Steps

After collecting data:

1. **Validate**: Run `notebooks/validation.ipynb`
2. **Enhance**: Add more derived features
3. **Train Models**: Use data for ML training (Step 2)
4. **Automate**: Schedule daily collection

## Troubleshooting

**"Riot API key not configured"**
→ Add key to `.env` or `config/config.yaml`

**"Rate limit exceeded"**
→ System auto-retries, or reduce `requests_per_second` in config

**"No matches collected"**
→ Check region has active players, verify queue_id

**"Import errors"**
→ Run from project root: `pip install -e .`

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for more help.

## Production Deployment

### Docker Deployment

```bash
# 1. Copy environment configuration
cp env.example .env
# Edit .env with your production settings

# 2. Build and start all services
docker-compose up --build

# 3. Verify deployment
curl http://localhost:8000/healthz
curl http://localhost:3000
```

### Monitoring

- **Metrics**: http://localhost:8000/metrics (Prometheus format)
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=src

# Run security tests
pytest tests/test_security.py

# Dependency scanning
pip-audit
safety check
```

## Security

### Security Features

- **Request Validation**: All inputs validated against schemas
- **Rate Limiting**: Per-IP and per-API-key limits
- **Payload Size Limits**: 32KB maximum request size
- **Request Timeouts**: 3-second timeout per request
- **CORS Protection**: Configurable origin allowlist
- **Log Sanitization**: Sensitive data removed from logs
- **Dependency Scanning**: Automated vulnerability detection

### Security Recommendations

1. **API Keys**: Use strong, unique API keys in production
2. **CORS Origins**: Restrict to your domain only
3. **HTTPS**: Always use HTTPS in production
4. **Firewall**: Restrict access to necessary ports only
5. **Updates**: Regularly update dependencies
6. **Monitoring**: Monitor logs and metrics for anomalies

### Environment Variables

```bash
# Required
API_KEY=your-secure-api-key-here
CORS_ORIGINS=https://yourdomain.com

# Security
MAX_PAYLOAD_SIZE=32768
REQUEST_TIMEOUT=3
SANITIZE_LOGS=true

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
```

## Requirements

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Riot Games API key (free at https://developer.riotgames.com/)
- ~5-10 GB disk space for data

## License

This project is for educational purposes. Respect Riot's API terms of service.

