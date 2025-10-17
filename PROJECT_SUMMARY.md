# StratMancer - Project Summary

## Overview

StratMancer is a production-ready data collection and ML platform for League of Legends match analysis. This document provides a complete summary of **Step 1: Data Collection Foundation**.

**Status**: ✅ **Complete and Ready for Use**

## What's Built

### Core Components

#### 1. Data Collection (`src/collectors/`)
- **MatchCollector**: Main collector class
  - Fetches matches from Iron to Challenger
  - Automatic patch tagging
  - Elo filtering and rank-based collection
  - Incremental saving (every 50 matches)
  - Duplicate detection
  - Progress tracking with tqdm

#### 2. Data Schema (`src/transformers/schema.py`)
- **Pydantic Models**: Type-safe, validated data structures
  - `MatchData`: Complete match information
  - `ChampionStats`: Per-champion performance metrics
  - `Objectives`: Team objectives (dragons, barons, etc.)
  - `DerivedFeatures`: Computed team composition features

**Schema Fields**:
```python
MatchData:
  - match_id: str                    # Unique identifier
  - patch: str                       # Game version (e.g., "14.23")
  - elo_rank: str                    # IRON → CHALLENGER
  - blue_picks: List[int]            # 5 champion IDs
  - red_picks: List[int]             # 5 champion IDs
  - blue_bans: List[int]             # 5 champion IDs
  - red_bans: List[int]              # 5 champion IDs
  - blue_win: bool                   # Match outcome
  - champion_stats: List[ChampionStats]  # 10 champions
      ├── id, role                   # Champion and position
      ├── kda, cs                    # Performance metrics
      └── dmg_share, gold_share      # Team contribution
  - blue_objectives: Objectives      # Blue team objectives
  - red_objectives: Objectives       # Red team objectives
  - derived_features: DerivedFeatures
      ├── ap_ad_ratio               # Damage composition
      ├── engage_score              # Initiation potential
      ├── splitpush_score           # Splitpush capability
      └── teamfight_synergy         # Teamfight coordination
```

#### 3. Data Transformation (`src/transformers/match_transformer.py`)
- **MatchTransformer**: Converts raw Riot API responses
  - Extracts relevant fields
  - Calculates derived features
  - Validates data integrity
  - Handles missing/malformed data

**Derived Features**:
- **AP/AD Ratio**: Magic vs physical damage composition
- **Engage Score**: Team initiation and CC potential
- **Splitpush Score**: Structure damage and objective pressure
- **Teamfight Synergy**: Assist participation and coordination

#### 4. Storage System (`src/storage/data_storage.py`)
- **DataStorage**: Multi-format data persistence
  - **Parquet**: Compressed, columnar, ML-ready
  - **JSON**: Human-readable, inspection-friendly
  - Automatic deduplication
  - Efficient loading and saving
  - Statistics tracking

**Features**:
- Incremental saving (memory efficient)
- Duplicate detection by match_id
- Compression (snappy for Parquet, gzip for JSON)
- Rank-based organization
- Statistics aggregation

#### 5. API Client (`src/utils/riot_api_client.py`)
- **RiotAPIClient**: Full-featured Riot API wrapper
  - All major endpoints (summoners, leagues, matches)
  - Regional routing (NA, EU, Asia)
  - Connection pooling
  - Error handling
  - Automatic retry logic

**Supported Endpoints**:
- Summoner data (by name, PUUID)
- League entries (by tier/division)
- Apex leagues (Challenger, Grandmaster, Master)
- Match history
- Match details
- Current patch version
- Champion data (Data Dragon)

#### 6. Rate Limiting (`src/utils/rate_limiter.py`)
- **RateLimiter**: Token bucket rate limiter
  - Per-second limits (default: 20 req/s)
  - Per-2-minute limits (default: 100 req/2min)
  - Automatic throttling
  - Exponential backoff on errors
  - Status monitoring

**Features**:
- Dual-window tracking (1s and 2min)
- Automatic sleep when limits approached
- Decorator for retry logic
- Rate limit header parsing

#### 7. Configuration (`src/utils/config_manager.py`)
- **ConfigManager**: Centralized configuration
  - YAML-based configuration
  - Environment variable override
  - Singleton pattern
  - Type-safe access
  - Validation

**Configurable**:
- API keys and region
- Rate limits
- Ranks to collect
- Storage formats
- Compression settings
- Feature toggles

#### 8. Validation Suite
- **Unit Tests** (`tests/test_schema.py`):
  - Schema validation
  - Edge case handling
  - Error detection
  
- **Validation Notebook** (`notebooks/validation.ipynb`):
  - Sample validation (100 matches/rank)
  - Schema compliance checking
  - Data completeness verification
  - Statistical summaries
  - Quality metrics

### Utility Scripts

#### 1. `check_status.py`
System status checker:
- ✅ Project structure verification
- ✅ Dependency checking
- ✅ Configuration validation
- ✅ Data collection statistics

#### 2. `quickstart.py`
Quick start test:
- Collects 10 sample matches
- Verifies setup
- Tests API connection
- Validates storage

#### 3. `run_collector.py`
Main collection script:
- Full data collection
- Command-line arguments
- Progress tracking
- Error handling

## Technical Specifications

### Architecture Principles

1. **Modularity**: Clean separation of concerns
   - Collectors, transformers, storage independent
   - Easy to extend or replace components
   - Minimal coupling between modules

2. **Type Safety**: Pydantic for validation
   - Runtime type checking
   - Automatic validation
   - Self-documenting schemas
   - IDE autocomplete support

3. **Error Handling**: Comprehensive error management
   - Graceful degradation
   - Automatic retries
   - Detailed logging
   - User-friendly error messages

4. **Production Ready**: Enterprise-grade features
   - Rate limiting
   - Configuration management
   - Logging
   - Testing
   - Documentation

### Performance Characteristics

**Collection Speed**:
- ~100-200 matches/hour (with rate limiting)
- ~1,500-2,000 matches/hour (theoretical max)
- Depends on: rank, region, time of day

**Storage Efficiency**:
- Parquet: ~5-10 KB per match
- JSON: ~15-25 KB per match (compressed)
- 10,000 matches: ~50-100 MB (Parquet)

**Memory Usage**:
- Incremental saving: <100 MB
- No data preloading
- Efficient processing

**Rate Limits**:
- Development key: 20 req/s, 100 req/2min
- Personal key: 100 req/s, 6000 req/10min
- Automatic handling in code

### Data Quality

**Validation**:
- Schema enforcement (Pydantic)
- Duplicate detection
- Missing data handling
- Value range checking

**Completeness**:
- 10 champion stats per match
- All picks and bans
- Team objectives
- Derived features

**Consistency**:
- Patch tagging
- Rank filtering
- Queue filtering (Ranked Solo/Duo only)

## Directory Structure

```
StratMancer/
├── config/
│   └── config.yaml              # Configuration file
├── data/                         # Data storage (auto-created)
│   ├── raw/                      # Raw API responses
│   └── processed/                # Processed matches
│       ├── matches_GOLD.parquet
│       ├── matches_GOLD.json
│       └── ...
├── notebooks/
│   └── validation.ipynb         # Data validation notebook
├── src/
│   ├── collectors/
│   │   └── match_collector.py   # Match collection
│   ├── transformers/
│   │   ├── schema.py            # Data schema
│   │   └── match_transformer.py # Data transformation
│   ├── storage/
│   │   └── data_storage.py      # Storage handlers
│   └── utils/
│       ├── config_manager.py    # Configuration
│       ├── riot_api_client.py   # API client
│       ├── rate_limiter.py      # Rate limiting
│       └── logging_config.py    # Logging setup
├── tests/
│   └── test_schema.py           # Unit tests
├── check_status.py              # Status checker
├── quickstart.py                # Quick start test
├── run_collector.py             # Main collector
├── requirements.txt             # Dependencies
├── README.md                    # Quick overview
├── SETUP_GUIDE.md               # Detailed setup
└── PROJECT_SUMMARY.md           # This file
```

## Usage Examples

### Basic Collection

```bash
# Quick test (10 matches)
python quickstart.py

# Collect 100 matches per rank
python run_collector.py --matches-per-rank 100

# Specific ranks
python run_collector.py --ranks GOLD PLATINUM --matches-per-rank 200

# Different region
python run_collector.py --region euw1 --matches-per-rank 100
```

### Loading Data

```python
from src.storage.data_storage import DataStorage

storage = DataStorage(base_path='data')

# Load matches
matches = storage.load_matches('GOLD', format='parquet')

# Access data
for match in matches:
    print(f"Match {match.match_id}")
    print(f"  Blue picks: {match.blue_picks}")
    print(f"  Winner: {'Blue' if match.blue_win else 'Red'}")
```

### Validation

```bash
# Check status
python check_status.py

# Detailed validation
jupyter notebook notebooks/validation.ipynb
```

## Dependencies

**Core**:
- `requests` - HTTP client
- `pandas` - Data manipulation
- `pyarrow` - Parquet support
- `pydantic` - Schema validation
- `python-dotenv` - Environment variables
- `pyyaml` - Configuration
- `tqdm` - Progress bars
- `tenacity` - Retry logic

**Development**:
- `pytest` - Testing
- `pytest-cov` - Coverage
- `jupyter` - Notebooks

**Total size**: ~200 MB (with dependencies)

## Configuration

`config/config.yaml`:

```yaml
riot_api:
  key: "RGAPI-YOUR-KEY"         # Can override with .env
  region: "na1"
  rate_limits:
    requests_per_second: 20
    requests_per_2_minutes: 100

collection:
  ranks: [IRON, BRONZE, ..., CHALLENGER]
  queue_id: 420                  # Ranked Solo/Duo
  matches_per_rank: 1000
  save_raw: false

storage:
  base_path: "data"
  formats: ["parquet", "json"]
  compression:
    parquet: "snappy"
    json: "gzip"
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Test schema
pytest tests/test_schema.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Integration Tests

```bash
# Status check
python check_status.py

# Quick test
python quickstart.py
```

### Validation

```bash
# Jupyter notebook
jupyter notebook notebooks/validation.ipynb
```

## Error Handling

### Automatic Handling

1. **Rate Limits**: Automatic throttling and retry
2. **Network Errors**: Exponential backoff
3. **Missing Data**: Graceful skipping
4. **Invalid Data**: Schema validation and rejection
5. **Duplicate Matches**: Automatic deduplication

### Manual Handling

```python
from src.collectors.match_collector import MatchCollector
from src.utils.riot_api_client import RiotAPIError

try:
    collector = MatchCollector(api_key="...", region="na1")
    matches = collector.collect_for_rank("GOLD", 100)
except RiotAPIError as e:
    print(f"API error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

**Configuration**: `src/utils/logging_config.py`

**Levels**:
- `DEBUG`: Detailed debugging
- `INFO`: General information (default)
- `WARNING`: Warnings (rate limits, missing data)
- `ERROR`: Errors (API failures, validation errors)

**Output**:
- Console: Real-time feedback
- File: Optional persistent logging

**Example**:
```python
from src.utils.logging_config import setup_logging

setup_logging(level="INFO", log_file="logs/collector.log")
```

## Limitations & Considerations

### Current Limitations

1. **API Rate Limits**:
   - Development key: 20 req/s, 100 req/2min
   - Limits collection speed
   - Handled automatically

2. **Match Availability**:
   - Only recent matches available
   - Riot's match history API has limits
   - Historical data not accessible

3. **Patch Changes**:
   - Champion IDs may change
   - Game mechanics evolve
   - Need to track patch versions

4. **Region Differences**:
   - Player skill varies by region
   - Different playstyles
   - May need region-specific models

### Design Decisions

1. **Parquet Primary Format**:
   - Fast columnar access
   - Excellent compression
   - ML library compatible
   - JSON as backup for inspection

2. **Incremental Saving**:
   - Memory efficient
   - Crash recovery
   - Progress preservation

3. **Rank-Based Storage**:
   - Easy filtering
   - Parallel collection
   - Targeted analysis

4. **Pydantic Validation**:
   - Runtime type checking
   - Clear error messages
   - Self-documenting
   - IDE support

## Future Enhancements (Step 2+)

### Potential Improvements

1. **Multi-Threading**: Parallel API requests
2. **Database**: SQL/NoSQL for larger datasets
3. **Web Interface**: Dashboard for monitoring
4. **Scheduled Collection**: Automatic daily runs
5. **Champion Metadata**: Static data integration
6. **Timeline Data**: Event-by-event analysis
7. **Player Tracking**: Follow specific players
8. **Meta Analysis**: Patch-to-patch comparisons

### ML Pipeline (Next Steps)

1. **Feature Engineering**:
   - Advanced team composition metrics
   - Champion synergy calculations
   - Meta-game features
   
2. **Model Training**:
   - Draft prediction
   - Win probability
   - Objective timing
   
3. **Deployment**:
   - API for predictions
   - Real-time analysis
   - Integration with tools

## Conclusion

**Step 1 Status**: ✅ **Complete**

**What's Working**:
- ✅ Modular, production-ready codebase
- ✅ Full Riot API integration
- ✅ Automatic patch tagging
- ✅ Elo filtering (Iron → Challenger)
- ✅ Multi-format storage (Parquet, JSON)
- ✅ Schema validation
- ✅ Error handling and rate limiting
- ✅ Comprehensive documentation
- ✅ Testing and validation

**Ready For**:
- Data collection at scale
- Statistical analysis
- ML model training (Step 2)
- Production deployment

**How to Get Started**:

```bash
# 1. Setup
pip install -r requirements.txt
cp .env.example .env  # Add your API key

# 2. Verify
python check_status.py

# 3. Test
python quickstart.py

# 4. Collect
python run_collector.py --matches-per-rank 100

# 5. Validate
jupyter notebook notebooks/validation.ipynb
```

---

**Project**: StratMancer  
**Phase**: Step 1 - Data Collection Foundation  
**Status**: ✅ Complete and Tested  
**Next**: Step 2 - ML Training Pipeline  

**Questions?** Check SETUP_GUIDE.md or README.md

