# Quick Command Reference - Rich Features

## 🚀 Complete Implementation (Copy-Paste)

### Step 1: Install Dependencies
```bash
pip install numpy pandas scikit-learn xgboost matplotlib seaborn tqdm
```

### Step 2: Build Assets for All ELOs
```bash
# Low ELO (Iron/Bronze/Silver)
python -m ml_pipeline.features.build_assets --elo low --patch 15.20 --embedding-dim 32 --min-samples 200

# Mid ELO (Gold/Platinum/Emerald) - YOUR MAIN ELO
python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200

# High ELO (Diamond+)
python -m ml_pipeline.features.build_assets --elo high --patch 15.20 --embedding-dim 32 --min-samples 200
```

### Step 3: Train Rich Models
```bash
# Low ELO
python -m ml_pipeline.models.train --model xgb --elo low --features rich --use-embeddings --use-matchups --use-synergy --ban-context

# Mid ELO (Gold rank - YOUR MAIN MODEL)
python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context

# High ELO
python -m ml_pipeline.models.train --model xgb --elo high --features rich --use-embeddings --use-matchups --use-synergy --ban-context
```

### Step 4: Evaluate Models
```bash
# Mid ELO evaluation (check quality gates)
python -m ml_pipeline.models.evaluate --models_dir ml_pipeline/models/trained --elo mid --report ece

# Low ELO
python -m ml_pipeline.models.evaluate --models_dir ml_pipeline/models/trained --elo low --report ece

# High ELO
python -m ml_pipeline.models.evaluate --models_dir ml_pipeline/models/trained --elo high --report ece
```

### Step 5: Restart Backend & Test
```bash
# Restart backend to load new models
python start_api.py

# In new terminal: Start frontend
cd frontend
npm run dev

# Open browser: http://localhost:3000/draft
```

---

## 🔄 Future Updates

### When You Collect More Data
```bash
# 1. Rebuild assets
python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200

# 2. Retrain model
python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context

# 3. Restart backend
python start_api.py
```

### When New Patch Releases (e.g., 15.21)
```bash
# 1. Collect data for new patch
python run_collector.py --ranks GOLD PLATINUM EMERALD --matches-per-rank 500

# 2. Build new patch assets
python -m ml_pipeline.features.build_assets --elo mid --patch 15.21 --embedding-dim 32 --min-samples 200

# 3. Retrain
python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context

# 4. Restart backend
python start_api.py
```

---

## 📊 Check Status

### Verify Assets Exist
```bash
dir data\assets
```
**Should show**:
- `matchups_mid_15.20.npz`
- `embeddings_mid.npy`
- `priors_mid_15.20.json`

### Verify Models Exist
```bash
dir ml_pipeline\models\trained
```
**Should show**:
- `model_mid_xgb_<timestamp>.pkl`
- `calibrator_mid_<timestamp>.pkl`

### Check Model Quality
```bash
python -c "import json; print(json.dumps(json.load(open('ml_pipeline/models/modelcards/modelcard_mid_<timestamp>.json')), indent=2))"
```
**Look for**:
- `roc_auc`: >0.60 ✅
- `brier_score`: <0.24 ✅
- `ece_raw`: ~0.04-0.05 ✅

---

## 🐛 Troubleshooting

### If recommendations still showing 0.0%
```bash
# Check backend logs for this line:
# "Using raw probability for recommendations: 0.5234"

# If you see "Using calibrated probability", that's wrong!
# Check backend/services/recommender.py line 142
```

### If model loading fails
```bash
# List available models
dir ml_pipeline\models\trained

# Check if backend is looking in right place
# backend/config.py: MODEL_DIR should be "ml_pipeline/models/trained"
```

### If assets not found during training
```bash
# Verify assets directory
dir data\assets

# If empty, rebuild:
python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200
```

---

## ✅ Success Indicators

After implementing rich features, you should see:

### In Terminal (Training)
```
INFO - Feature vector length: 487 dimensions  # (not 338)
INFO - Model ROC-AUC: 0.6234  # (not 0.52)
INFO - ECE (calibrated): 0.0423  # (not 0.15)
```

### In UI (Draft Analyzer)
- Confidence: **20-45%** (not 5-16%)
- Win probabilities: **45-65%** (not always 50%)
- Key factors: Shows **duo synergy**, **matchup advantage** (not just champion names)

### In Recommendations
- Ban suggestions: **3-9% threat reduction** (varied)
- Pick suggestions: **1.5-5.5% win gain** (not all 0.0%)
- Explanations: Mention **"synergy"**, **"favorable matchup"** (not generic)

---

## 🎯 One-Liner for Quick Retrain

```bash
python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200 && python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context && python start_api.py
```

---

## 📈 Recommended Data Collection Target

**Current**: ~500-1600 matches per ELO
**Target for Production**: 3000-5000 matches per ELO

```bash
# Collect 2000 more Gold/Plat/Emerald matches
python run_collector.py --ranks GOLD PLATINUM EMERALD --matches-per-rank 700
```

**Why**: More data = better matchup statistics, more robust embeddings, higher confidence predictions.

---

## 💡 Pro Tips

1. **Always build assets before training** - Training will fallback to basic features if assets missing
2. **Evaluate before deploying** - Check ECE and gate results
3. **Keep old models** - Compare new vs old ROC-AUC to ensure improvement
4. **Collect across patches** - Diversifies meta snapshots
5. **Monitor backend logs** - Watch for "Using raw probability" in recommender logs

---

## 📝 Files to Check

- `RICH_FEATURES_GUIDE.md` - Full detailed guide
- `ml_pipeline/features/build_assets.py` - Asset builder source
- `ml_pipeline/models/train.py` - Training pipeline
- `backend/services/inference.py` - Serving logic
- `backend/services/recommender.py` - Recommendation engine

