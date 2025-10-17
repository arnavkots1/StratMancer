# StratMancer Setup Guide

Complete guide to get your League of Legends ML platform running.

## Prerequisites

- Python 3.8 or higher (3.13 recommended)
- Riot Games API key (free at https://developer.riotgames.com/)
- ~5-10 GB disk space for data
- Internet connection

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Note**: If using a virtual environment (recommended):

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Your Riot API Key

1. Go to https://developer.riotgames.com/
2. Sign in with your Riot account
3. Register an application
4. Copy your API key (starts with `RGAPI-`)

**Important**: Development keys expire after 24 hours. For long-term projects:
- Request a Personal API key (good for longer periods)
- Or regenerate the key daily

### 3. Configure API Key

**Option A: Using .env file (Recommended)**

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env    # Windows
# or
cp .env.example .env      # Mac/Linux
```

Edit `.env` and add your key:

```
RIOT_API_KEY=RGAPI-your-actual-key-here
```

**Option B: Using config.yaml**

Edit `config/config.yaml`:

```yaml
riot_api:
  key: "RGAPI-your-actual-key-here"
  region: "na1"
```

### 4. Verify Setup

```bash
python check_status.py
```

You should see:
```
✅ Project Structure............ PASS
✅ Dependencies................ PASS
✅ Configuration............... PASS
⚠️  Data Collection............ (No data yet)
```

### 5. Test Collection

Collect 10 test matches:

```bash
python quickstart.py
```

This will:
- Verify your API key works
- Collect 10 matches from Gold rank
- Save them to `data/processed/`
- Show you the data structure

Expected output:
```
✅ API key configured
✅ Collector initialized (patch 14.23)
✅ Collected 10 matches successfully!
```

## Full Data Collection

### Basic Collection

```bash
# Collect 100 matches per rank (all ranks)
python run_collector.py --matches-per-rank 100

# Collect from specific ranks only
python run_collector.py --ranks GOLD PLATINUM DIAMOND --matches-per-rank 100

# Different region
python run_collector.py --region euw1 --matches-per-rank 100
```

### Advanced Options

```bash
# Save raw API responses for debugging
python run_collector.py --save-raw --matches-per-rank 50

# Multiple regions (run separately)
python run_collector.py --region na1 --matches-per-rank 200
python run_collector.py --region euw1 --matches-per-rank 200
python run_collector.py --region kr --matches-per-rank 200
```

### Collection Tips

**Time Estimates**:
- 100 matches: ~5-10 minutes
- 1,000 matches: ~30-60 minutes
- 10,000 matches: ~5-10 hours

**Rate Limits**:
- Development key: 20 requests/second, 100 requests/2 minutes
- The system handles this automatically with built-in rate limiting

**What's Collected**:
- Ranked Solo/Duo matches only (queue ID 420)
- Current patch by default
- All ranks from Iron to Challenger
- Complete match data including picks, bans, stats, objectives

## Validate Your Data

### Quick Validation

```bash
python check_status.py
```

Shows match counts by rank and patch.

### Detailed Validation

```bash
jupyter notebook notebooks/validation.ipynb
```

This notebook:
- Loads 100 matches per rank
- Validates schema compliance
- Checks data completeness
- Shows statistical summaries
- Verifies data quality

## Troubleshooting

### "Riot API key not configured"

**Solution**: 
1. Check your `.env` file exists and contains `RIOT_API_KEY=RGAPI-...`
2. Or update `config/config.yaml` with your key
3. Make sure there are no extra spaces or quotes around the key

### "Rate limit exceeded"

**Solution**: 
- The system automatically retries with exponential backoff
- If it persists, reduce `requests_per_second` in `config/config.yaml`:
  ```yaml
  riot_api:
    rate_limits:
      requests_per_second: 10  # Reduce from 20
  ```

### "No matches collected"

**Possible causes**:
1. **Wrong region**: Verify region has active players (try `na1`, `euw1`, or `kr`)
2. **API key expired**: Development keys expire after 24 hours
3. **Network issues**: Check internet connection

**Solution**:
```bash
# Try a major region
python run_collector.py --region na1 --ranks GOLD --matches-per-rank 10

# Check logs for specific errors
# Logs are shown in console during collection
```

### "Import errors" or "Module not found"

**Solution**:
```bash
# Make sure you're in the project root
cd path/to/StratMancer

# Reinstall dependencies
pip install -r requirements.txt

# If using venv, make sure it's activated
```

### "No module named 'src'"

**Solution**: Always run scripts from the project root:
```bash
# Correct:
python run_collector.py

# Wrong:
cd src
python ../run_collector.py  # This will fail
```

### Collection is slow

**Normal behavior**:
- ~100-200 matches/hour with rate limiting
- Fetching from high ranks (Challenger, Grandmaster) takes longer
- First collection is slower as it finds active players

**To speed up**:
- Focus on specific ranks: `--ranks GOLD PLATINUM DIAMOND`
- Skip raw data saving: Remove `--save-raw` flag
- Use major regions (more active players): `na1`, `euw1`, `kr`

## Configuration Options

Edit `config/config.yaml`:

```yaml
# API Settings
riot_api:
  key: "RGAPI-YOUR-KEY"
  region: "na1"              # na1, euw1, kr, br1, etc.
  rate_limits:
    requests_per_second: 20   # Adjust if hitting limits
    requests_per_2_minutes: 100

# Collection Settings
collection:
  ranks:                      # Ranks to collect
    - "GOLD"
    - "PLATINUM"
    - "DIAMOND"
  queue_id: 420              # 420 = Ranked Solo/Duo
  matches_per_rank: 1000     # Target per rank
  save_raw: false            # Save raw API responses

# Storage Settings  
storage:
  base_path: "data"
  formats:
    - "parquet"              # ML-ready format
    - "json"                 # Human-readable format
  compression:
    parquet: "snappy"
    json: "gzip"
```

## Data Structure

After collection, your data structure:

```
data/
├── raw/                    # Raw API responses (if save_raw: true)
│   └── NA1_1234567890.json
└── processed/              # Processed matches
    ├── matches_GOLD.parquet
    ├── matches_GOLD.json
    ├── matches_PLATINUM.parquet
    └── ...
```

## Loading Data in Python

```python
from src.storage.data_storage import DataStorage

# Initialize storage
storage = DataStorage(base_path='data')

# Load matches for a rank
gold_matches = storage.load_matches('GOLD', format='parquet')

# Access match data
for match in gold_matches[:10]:
    print(f"Match: {match.match_id}")
    print(f"  Patch: {match.patch}")
    print(f"  Rank: {match.elo_rank}")
    print(f"  Blue win: {match.blue_win}")
    print(f"  Blue picks: {match.blue_picks}")
    print(f"  Objectives: {match.blue_objectives.dragons} dragons")
    print(f"  AP/AD ratio: {match.derived_features.ap_ad_ratio}")
    print()

# Get statistics
stats = storage.get_statistics()
print(f"Total matches: {stats['total_matches']}")
print(f"By rank: {stats['by_rank']}")
print(f"By patch: {stats['by_patch']}")
```

## Best Practices

### API Key Security

**DO**:
- Use `.env` file for API keys
- Add `.env` to `.gitignore` (already done)
- Regenerate keys if exposed

**DON'T**:
- Commit API keys to git
- Share keys publicly
- Hardcode keys in source files

### Data Collection

**DO**:
- Start with small test (10-50 matches)
- Collect regularly (daily/weekly)
- Use multiple regions for diversity
- Monitor rate limits

**DON'T**:
- Exceed rate limits unnecessarily
- Ignore patch changes (data becomes incompatible)
- Mix patches without filtering

### Data Organization

**DO**:
- Separate by patch version
- Filter by rank for targeted analysis
- Keep raw data for debugging (if space allows)
- Validate data before ML training

**DON'T**:
- Mix different patches
- Delete raw data before validation
- Ignore schema validation errors

## Performance Tips

### Faster Collection

1. **Focus on active ranks**: Gold, Platinum, Diamond have most players
2. **Use major regions**: NA1, EUW1, KR have more active players
3. **Collect in parallel**: Run multiple collectors for different regions
4. **Skip raw storage**: Don't use `--save-raw` unless debugging

### Memory Optimization

1. **Incremental saving**: System auto-saves every 50 matches
2. **Load by rank**: Don't load all data at once
3. **Use Parquet**: More memory efficient than JSON

### Storage Optimization

1. **Parquet compression**: Already configured (snappy)
2. **Remove old patches**: Delete data from outdated patches
3. **Skip raw data**: Set `save_raw: false` in config

## Next Steps

After successful data collection:

1. **Validate Data**: 
   ```bash
   jupyter notebook notebooks/validation.ipynb
   ```

2. **Analyze Patterns**:
   - Win rates by champion
   - Objective importance by rank
   - Team composition synergies

3. **Prepare for ML**:
   - Feature engineering
   - Data splitting (train/val/test)
   - Model training (Step 2)

4. **Automate Collection**:
   - Schedule daily runs
   - Monitor data quality
   - Handle patch updates

## Support

### Documentation

- **README.md**: Quick overview
- **ARCHITECTURE.md**: Technical details
- **PROJECT_SUMMARY.md**: Complete feature list

### Common Issues

Check the troubleshooting section above. Most issues are:
1. API key configuration
2. Rate limiting
3. Import paths

### Riot API Resources

- Developer Portal: https://developer.riotgames.com/
- API Documentation: https://developer.riotgames.com/apis
- Status Page: https://developer.riotgames.com/api-status
- Community: https://discord.gg/riotgamesdevrel

## License & Terms

This project is for educational purposes. Respect Riot's API terms:
- Don't spam requests
- Don't commercialize without permission
- Follow rate limits
- Credit Riot Games

---

**Ready to collect data?**

```bash
# Verify setup
python check_status.py

# Test collection
python quickstart.py

# Full collection
python run_collector.py --matches-per-rank 100
```

Good luck with your ML project! 🚀



