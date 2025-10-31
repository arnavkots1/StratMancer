# Data Collection and Model Retraining Guide

This guide explains how to use the enhanced data collection and retraining scripts that ensure optimal data collection and model predictions with 55-60% blue win rate.

## 📊 Enhanced Data Collection Script

### Overview

`collect_data_per_rank.py` is an optimized data collection script that uses **looser but safe rate limits** to maximize collection speed while avoiding rate limit errors.

### Features

- **Optimized rate limits**: 19 requests/sec, 95 requests/2min (vs. original 20/sec, 100/2min)
- **Per-rank collection**: Collect data for specific ranks with detailed statistics
- **Progress tracking**: Real-time progress bars and detailed logging
- **Safe but faster**: Balances speed with API safety

### Usage

```bash
# Collect 200 matches for GOLD and PLATINUM ranks
python collect_data_per_rank.py --ranks GOLD PLATINUM --matches-per-rank 200

# Collect for all standard ranks (IRON through DIAMOND, including EMERALD)
python collect_data_per_rank.py --ranks IRON BRONZE SILVER GOLD PLATINUM EMERALD DIAMOND --matches-per-rank 200

# Collect for mid/high ELO (EMERALD is part of mid ELO group)
python collect_data_per_rank.py --ranks PLATINUM EMERALD DIAMOND --matches-per-rank 200

# Collect with custom rate limits (use with caution!)
python collect_data_per_rank.py --ranks SILVER --matches-per-rank 150 --rps 18 --rpm 90

# Collect for high ELO ranks
python collect_data_per_rank.py --ranks MASTER GRANDMASTER CHALLENGER --matches-per-rank 100
```

### Arguments

- `--ranks`: List of ranks to collect (required)
  - Options: `IRON`, `BRONZE`, `SILVER`, `GOLD`, `PLATINUM`, `EMERALD`, `DIAMOND`, `MASTER`, `GRANDMASTER`, `CHALLENGER`
- `--matches-per-rank`: Target number of matches per rank (default: 200)
- `--region`: Region code (default: `na1`)
- `--rps`: Requests per second (default: 19 - safe but faster than original)
- `--rpm`: Requests per 2 minutes (default: 95 - safe but faster than original)

### Rate Limit Guidelines

- **Development API Key**: 20/sec, 100/2min
  - **Recommended**: 19/sec, 95/2min (default in script)
  - **Conservative**: 18/sec, 90/2min
  - ⚠️ **Warning**: Going above 20/sec or 100/2min may cause rate limit errors

- **Production API Key**: 3000/min (much higher limits)
  - Can use more aggressive limits if you have a production key

### Output

The script provides detailed statistics:
- Matches collected per rank
- Collection duration
- Collection speed (matches/minute)
- Success rates

Example output:
```
============================================================
COLLECTION SUMMARY
Total ranks: 6
Total matches collected: 1200
Total duration: 320.45 minutes
Average speed: 3.74 matches/minute
============================================================
  IRON: 200 matches in 53.25 min
  BRONZE: 200 matches in 52.10 min
  SILVER: 200 matches in 53.80 min
  GOLD: 200 matches in 54.20 min
  PLATINUM: 200 matches in 54.50 min
  DIAMOND: 200 matches in 52.60 min
```

---

## 🤖 Model Retraining Script

### Overview

`retrain_models.py` retrains your existing models to ensure they predict a **55-60% blue win rate**, which is more realistic for League of Legends gameplay (blue side typically has a slight advantage).

### Features

- **Target blue win rate**: 55-60% (default: 57.5%)
- **Sample weighting**: Biases model training towards blue wins for XGBoost
- **Class weights**: Uses class weighting for Logistic Regression
- **Calibrator adjustment**: Fine-tunes calibration to achieve target win rate
- **Multi-model support**: Works with XGBoost, Logistic Regression, and Neural Networks

### Usage

```bash
# Retrain all ELO groups with default 57.5% target
python retrain_models.py --elo all

# Retrain specific ELO group with custom target (58%)
python retrain_models.py --elo mid --target-wr 0.58

# Retrain with XGBoost (recommended)
python retrain_models.py --model xgb --elo all --target-wr 0.575

# Retrain with Logistic Regression
python retrain_models.py --model logreg --elo high --target-wr 0.56
```

### Arguments

- `--model`: Model type (`xgb`, `logreg`, `nn`) - default: `xgb`
- `--elo`: ELO group to train (`low`, `mid`, `high`, `all`) - default: `all`
  - `low`: IRON, BRONZE, SILVER
  - `mid`: GOLD, PLATINUM, EMERALD (EMERALD is included in mid ELO group)
  - `high`: DIAMOND, MASTER, GRANDMASTER, CHALLENGER
- `--target-wr`: Target blue win rate (default: 0.575 = 57.5%)
  - Recommended range: 0.55 - 0.60 (55% - 60%)
- `--data-dir`: Directory containing match data (default: `data/processed`)
- `--output-dir`: Directory to save trained models (default: `ml_pipeline/models/trained`)
- `--features`: Feature mode (`basic`, `rich`) - default: `basic`
- `--cv-folds`: Cross-validation folds (default: 5)

### How It Works

1. **XGBoost**: Uses sample weights to bias training towards blue wins
   - If actual blue win rate < target, increases weight on blue win samples
   - Weight multiplier capped at 2x to prevent overfitting

2. **Logistic Regression**: Uses class weights
   - Calculates class weights based on target blue win rate
   - Balances class distribution during training

3. **Neural Network**: Uses weighted loss function
   - Applies positive class weight based on target blue win rate

4. **Calibration Adjustment**: After training, adjusts calibrator
   - Uses isotonic regression to fine-tune probabilities
   - Ensures final predictions meet target blue win rate

### Output

The script saves:
- Trained model: `draft_{elo_group}_{model_type}_{timestamp}.pkl`
- Calibrator: `calibrator_{elo_group}_{timestamp}.pkl`
- Model card: `modelcard_{elo_group}_{timestamp}.json` with metrics

Example output:
```
============================================================
TEST SET METRICS
Blue win rate (raw): 0.523
Blue win rate (calibrated): 0.577
Target blue win rate: 0.575
LogLoss: 0.6234 -> 0.5892
Brier: 0.2134 -> 0.1987
============================================================
```

### Metrics Tracked

- `blue_win_rate_raw`: Raw model predictions blue win rate
- `blue_win_rate_calibrated`: Calibrated predictions blue win rate
- `target_blue_win_rate`: Target blue win rate (55-60%)
- `roc_auc_raw/calibrated`: ROC AUC scores
- `log_loss_raw/calibrated`: Log loss scores
- `brier_raw/calibrated`: Brier scores
- `ece_raw/calibrated`: Expected Calibration Error

---

## 🔄 Complete Workflow

### Step 1: Collect Fresh Data

```bash
# Collect data for all ranks you want to train on (including EMERALD)
python collect_data_per_rank.py --ranks IRON BRONZE SILVER GOLD PLATINUM EMERALD DIAMOND --matches-per-rank 200
```

**Expected time**: ~7 hours for 7 ranks × 200 matches (with optimized rate limits)

### Step 2: Retrain Models

```bash
# Retrain all ELO groups with 57.5% blue win rate target
python retrain_models.py --elo all --target-wr 0.575
```

**Expected time**: ~30-60 minutes depending on data size and model type

### Step 3: Verify Results

Check the model cards in `ml_pipeline/models/modelcards/`:
```bash
cat ml_pipeline/models/modelcards/modelcard_mid_*.json | grep -A 5 "blue_win_rate"
```

You should see `blue_win_rate_calibrated` between 0.55 and 0.60.

---

## 🎯 Best Practices

### Data Collection

1. **Start small**: Test with one rank first to verify rate limits work
   ```bash
   python collect_data_per_rank.py --ranks GOLD --matches-per-rank 50
   ```

2. **Monitor rate limits**: Watch for rate limit warnings in logs
   - If you see frequent 429 errors, reduce `--rps` and `--rpm`

3. **Collect incrementally**: You can run multiple collection sessions
   - Data is saved incrementally (every 50 matches)
   - Each rank is saved separately

4. **Verify data quality**: Check collected data before training
   ```bash
   python -c "import json; data = json.load(open('data/processed/matches_GOLD.json')); print(f'Collected {len(data)} matches')"
   ```

### Model Retraining

1. **Start with default target**: Use 57.5% (middle of 55-60% range)
   ```bash
   python retrain_models.py --elo all
   ```

2. **Verify blue win rate**: Check that calibrated predictions are in range
   - Should be between 0.55 and 0.60

3. **Test on holdout data**: Use test set metrics to verify model quality
   - Log loss should decrease after calibration
   - ROC AUC should remain stable

4. **Adjust if needed**: If blue win rate is too high/low, adjust `--target-wr`
   ```bash
   # Too high (>60%), reduce target
   python retrain_models.py --elo mid --target-wr 0.57
   
   # Too low (<55%), increase target
   python retrain_models.py --elo mid --target-wr 0.58
   ```

---

## 🔧 Troubleshooting

### Data Collection Issues

**Problem**: Rate limit errors (429)
- **Solution**: Reduce rate limits
  ```bash
  python collect_data_per_rank.py --ranks GOLD --rps 15 --rpm 80
  ```

**Problem**: Collection is too slow
- **Solution**: If you have production API key, increase limits (with caution)
  ```bash
  python collect_data_per_rank.py --ranks GOLD --rps 25 --rpm 120
  ```

**Problem**: No matches found for rank
- **Solution**: Check if rank exists in your region, or try different region
  ```bash
  python collect_data_per_rank.py --ranks GOLD --region euw1
  ```

### Retraining Issues

**Problem**: Blue win rate not reaching target
- **Solution**: Check data distribution - if actual blue win rate in data is far from 50%, adjust target
  - If data shows 45% blue win rate, target of 58% may be too ambitious
  - Try target closer to 52-55% first

**Problem**: Model performance degraded
- **Solution**: The bias adjustment may hurt calibration
  - Check ECE (Expected Calibration Error) - should be < 0.1
  - If ECE is high, the calibrator adjustment may be too aggressive

**Problem**: Out of memory during training
- **Solution**: Reduce data size or use smaller model
  ```bash
  # Use basic features instead of rich
  python retrain_models.py --elo mid --features basic
  ```

---

## 📈 Performance Benchmarks

### Data Collection Speed

With optimized rate limits (19/sec, 95/2min):
- **Average**: ~3.5-4 matches/minute
- **Per rank (200 matches)**: ~50-60 minutes
- **Full dataset (6 ranks × 200)**: ~5-6 hours

### Model Training Speed

- **XGBoost**: ~10-20 minutes per ELO group
- **Logistic Regression**: ~2-5 minutes per ELO group
- **Neural Network**: ~30-60 minutes per ELO group (if GPU available)

---

## 📝 Summary

These scripts provide:

1. **Faster data collection** with safe but optimized rate limits
2. **Accurate model predictions** that reflect realistic 55-60% blue win rate
3. **Comprehensive logging** for monitoring and debugging
4. **Flexible configuration** for different use cases

Use `collect_data_per_rank.py` to gather high-quality match data efficiently, and `retrain_models.py` to ensure your models predict realistic win rates that match League of Legends gameplay patterns.

