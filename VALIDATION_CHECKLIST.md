# Rich Features Validation Checklist

Use this checklist to verify everything is working after implementation.

---

## ✅ Pre-Implementation Checks

### 1. Dependencies Installed
```bash
python -c "import numpy, pandas, sklearn, xgboost, matplotlib, seaborn; print('✅ All dependencies installed')"
```
- [ ] Command runs without errors

### 2. Data Available
```bash
dir data\processed
```
- [ ] `matches_GOLD.json` exists
- [ ] `matches_PLATINUM.json` exists (if available)
- [ ] `matches_EMERALD.json` exists (if available)
- [ ] Files are not empty (should be >100KB each)

### 3. Feature Map Present
```bash
dir ml_pipeline\feature_map.json
```
- [ ] File exists and is >50KB

---

## ✅ Asset Building Checks

### 1. Run Asset Builder
```bash
python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200
```

**Expected output:**
```
INFO - Loaded 1637 matches for mid
INFO - Built matchup matrices for 5 roles
INFO - Generated 32-dim embeddings for 169 champions
INFO - Computed priors: 169 champions analyzed
INFO - Assets saved to data/assets/
```

- [ ] No errors or exceptions
- [ ] "Loaded X matches" shows >500 matches
- [ ] "Generated 32-dim embeddings" confirms embedding creation
- [ ] "Assets saved" confirms success

### 2. Verify Asset Files Created
```bash
dir data\assets
```
- [ ] `matchups_mid_15.20.npz` exists
- [ ] `embeddings_mid.npy` exists
- [ ] `priors_mid_15.20.json` exists
- [ ] Files are not empty (matchups should be >10KB, embeddings >200KB)

### 3. Inspect Priors JSON (Optional)
```bash
python -c "import json; p=json.load(open('data/assets/priors_mid_15.20.json')); print(f'Champions: {len(p)}, Sample: {list(p.items())[0]}')"
```
- [ ] Shows champion count (should be ~169)
- [ ] Shows sample champion with base_wr, pick_rate, trend_3patch

---

## ✅ Model Training Checks

### 1. Run Training
```bash
python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context
```

**Expected output:**
```
INFO - Loaded 1637 matches for ELO group: mid
INFO - Assembling rich features with context
INFO - Feature vector length: 487 dimensions
INFO - Running XGBoost grid search (5-fold CV)...
Best params: {'max_depth': 5, ...}
INFO - Model ROC-AUC: 0.6234, Brier: 0.2341, ECE: 0.0423
INFO - Saved model to ml_pipeline/models/trained/model_mid_xgb_<timestamp>.pkl
```

- [ ] "Feature vector length: 487" (NOT 338) - confirms rich features
- [ ] ROC-AUC >0.58
- [ ] Brier Score <0.25
- [ ] ECE <0.06
- [ ] Model saved successfully

### 2. Verify Model Files
```bash
dir ml_pipeline\models\trained
```
- [ ] `model_mid_xgb_<timestamp>.pkl` exists
- [ ] `calibrator_mid_<timestamp>.pkl` exists
- [ ] Model file is >1MB

### 3. Check Modelcard
```bash
dir ml_pipeline\models\modelcards
```
- [ ] `modelcard_mid_<timestamp>.json` exists
- [ ] File contains "roc_auc", "brier_score", "ece_raw", "ece_calibrated"

---

## ✅ Model Evaluation Checks

### 1. Run Evaluation
```bash
python -m ml_pipeline.models.evaluate --models_dir ml_pipeline/models/trained --elo mid --report ece
```

**Expected output:**
```
INFO - Loaded model: mid, type=xgb
INFO - Holdout metrics:
  ROC-AUC: 0.6234
  Brier Score: 0.2341
  ECE (calibrated): 0.0423
INFO - Gate evaluation: PASS
```

- [ ] ROC-AUC >0.58
- [ ] Brier Score <0.25
- [ ] ECE (calibrated) <0.05
- [ ] Gate status: PASS

### 2. Check Generated Plots
```bash
dir ml_pipeline\models\plots
```
- [ ] `mid_<timestamp>_roc.png` exists
- [ ] `mid_<timestamp>_calibration.png` exists
- [ ] `mid_<timestamp>_feature_importance.png` exists

### 3. Inspect Feature Importance (Optional)
Open `ml_pipeline/models/plots/mid_<timestamp>_feature_importance.png`
- [ ] Top features include "duo_synergy", "matchup", "embedding", "prior" (not just champion names)

---

## ✅ Backend Integration Checks

### 1. Verify Backend Code
Check `backend/services/inference.py` line 156:
```python
raw_prob, calibrated_prob = predict_raw_and_calibrated(...)
```
- [ ] Function call exists
- [ ] Returns both raw and calibrated probabilities

Check `backend/services/inference.py` line 165:
```python
selected_prob = calibrated_prob if calibrated_for_ui else raw_prob
```
- [ ] Toggle logic present

### 2. Verify Recommender Uses Raw Probs
Check `backend/services/recommender.py` line 151 and 184:
```python
calibrated_for_ui=False
```
- [ ] Set to `False` (uses raw probabilities for deltas)

### 3. Start Backend
```bash
python start_api.py
```
- [ ] Backend starts without errors
- [ ] Logs show "Model loaded for mid: xgb"
- [ ] No "Feature map is None" errors

---

## ✅ API Endpoint Checks

### 1. Test Prediction Endpoint
```bash
curl -X POST "http://localhost:8000/predict-draft" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-dev-key" ^
  -d "{\"elo\":\"mid\",\"patch\":\"15.20\",\"blue\":{\"top\":266,\"jgl\":64,\"mid\":103,\"adc\":498,\"sup\":412,\"bans\":[11,64,82,157,555]},\"red\":{\"top\":85,\"jgl\":121,\"mid\":238,\"adc\":22,\"sup\":53,\"bans\":[23,68,350,777,875]}}"
```

**Expected response:**
- [ ] `blue_win_prob`: between 0.40 and 0.65 (NOT 0.50 exactly)
- [ ] `confidence`: >10 (NOT 5-8)
- [ ] `explanations`: includes varied features (duo_synergy, matchup, etc.)
- [ ] `model_version`: contains timestamp

### 2. Test Pick Recommendation
```bash
curl -X POST "http://localhost:8000/recommend-pick" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-dev-key" ^
  -d "{\"elo\":\"mid\",\"patch\":\"15.20\",\"role\":\"top\",\"draft\":{\"blue\":{\"top\":-1,\"jgl\":64,\"mid\":103,\"adc\":498,\"sup\":412,\"bans\":[11,64,82,157,555]},\"red\":{\"top\":85,\"jgl\":121,\"mid\":238,\"adc\":22,\"sup\":53,\"bans\":[23,68,350,777,875]}}}"
```

**Expected response:**
- [ ] Returns 5 recommendations
- [ ] `win_gain` values are VARIED (e.g., 4.3, 3.7, 2.8, 2.1, 1.5) - NOT all 0.0 or 9.3
- [ ] `explanation` mentions synergy or matchup advantages

### 3. Check Backend Logs
Look for these lines in backend output:
```
INFO - Using raw probability for recommendations: 0.5234
INFO - Baseline win rate: 0.5123
INFO - Champion 266: win_gain=4.3%
```
- [ ] "Using raw probability" present (NOT "Using calibrated")
- [ ] Baseline win rate NOT always 0.5
- [ ] Win gains are varied (NOT all 0.0)

---

## ✅ Frontend UI Checks

### 1. Start Frontend
```bash
cd frontend
npm run dev
```
- [ ] Starts on http://localhost:3000

### 2. Navigate to Draft Analyzer
Open http://localhost:3000/draft
- [ ] Page loads without errors
- [ ] Champions load successfully
- [ ] "Start Draft" button present

### 3. Test Draft Flow
1. Click "Start Draft"
2. Ban 5 champions per team
3. Pick 5 champions per team
4. Click "Predict Draft"

**Expected behavior:**
- [ ] Prediction shows confidence **20-45%** (NOT 5-16%)
- [ ] Win probabilities are **NOT exactly 50/50**
- [ ] Key factors section shows meaningful insights (e.g., "Strong duo synergy", "Favorable mid matchup")
- [ ] Key factors do NOT all show 0.0% impact

### 4. Test Recommendations
During draft, after each ban/pick:

**Ban recommendations:**
- [ ] Show threat reduction **3-9%** (NOT all 0.0 or all 9.3)
- [ ] Values are VARIED across 5 recommendations
- [ ] Explanations mention specific threats

**Pick recommendations:**
- [ ] Show win gain **1.5-5.5%** (NOT all 0.0)
- [ ] Values are VARIED across 5 recommendations
- [ ] Explanations mention synergy or matchup advantages
- [ ] Champion images load correctly

### 5. Test Edge Cases
- [ ] Empty draft (before any picks) shows 50/50 baseline
- [ ] Partial draft (3 picks) shows meaningful probabilities
- [ ] Full draft (10 picks) shows confident prediction

---

## ✅ Quality Gates

### Model Performance
- [ ] ROC-AUC: **>0.58** (draft prediction threshold)
- [ ] Brier Score: **<0.25** (calibration quality)
- [ ] ECE: **<0.05** (probability reliability)
- [ ] Gate Status: **PASS** (LogLoss OR Brier improved >20%)

### UI Experience
- [ ] Confidence: **20-45%** (actionable predictions)
- [ ] Predictions: **40-65% win rate** (not always 50%)
- [ ] Recommendations: **Varied win gains** (not all same value)
- [ ] Explanations: **Feature-rich** (synergy, matchup, not generic)

### Backend Logs
- [ ] "Feature vector length: 487" during inference
- [ ] "Using raw probability" in recommender logs
- [ ] No "Feature map is None" errors
- [ ] No "Model not found" errors

---

## 🚨 Common Issues & Fixes

### Issue: Feature vector length is 338
**Cause**: Assets not loaded, falling back to basic features
**Fix**: 
1. Check `data/assets/` exists and has files
2. Verify training used `--features rich --use-embeddings --use-matchups --use-synergy`
3. Retrain model

### Issue: Recommendations still showing 0.0%
**Cause**: Model predicting extreme probabilities (0% or 100%)
**Fix**:
1. Check evaluation ECE score (<0.05 is good)
2. Verify recommender uses `calibrated_for_ui=False`
3. Ensure calibrator exists and is loaded
4. Retrain with more data if ECE >0.10

### Issue: ROC-AUC < 0.58
**Cause**: Insufficient data or poor feature quality
**Fix**:
1. Collect more matches (target 3000+ per ELO)
2. Rebuild assets with `--min-samples 500`
3. Check matchup matrices for sufficient data
4. Verify embeddings are 32 or 64 dim (not 0)

### Issue: "Assets not found" during training
**Cause**: Asset builder not run, or wrong patch/elo
**Fix**:
1. Run `python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200`
2. Check `data/assets/` contains files
3. Verify patch parameter matches training patch

---

## 📊 Success Metrics

### Before Rich Features
| Metric | Value | Status |
|--------|-------|--------|
| ROC-AUC | 0.52 | ❌ Below threshold |
| Brier Score | 0.28 | ❌ Poor calibration |
| ECE | 0.15 | ❌ Unreliable probs |
| UI Confidence | 5-16% | ❌ Too uncertain |
| Win Gain | 0.0-0.2% | ❌ Unhelpful |

### After Rich Features (Target)
| Metric | Value | Status |
|--------|-------|--------|
| ROC-AUC | 0.60-0.65 | ✅ Good discrimination |
| Brier Score | 0.22-0.24 | ✅ Well calibrated |
| ECE | 0.04-0.05 | ✅ Reliable probs |
| UI Confidence | 20-45% | ✅ Actionable |
| Win Gain | 1.5-5.5% | ✅ Meaningful |

---

## 🎯 Final Validation

**All systems GO if:**
1. ✅ Assets built for all ELOs
2. ✅ Models trained with 487-dim features
3. ✅ Evaluation shows ROC-AUC >0.58, ECE <0.05
4. ✅ Backend logs show "Using raw probability for recommendations"
5. ✅ UI shows varied win probabilities (not 50/50)
6. ✅ Recommendations show varied win gains (not 0.0%)
7. ✅ Explanations mention synergy/matchup insights

**If ANY checks fail**, refer to `RICH_FEATURES_GUIDE.md` for detailed troubleshooting.

---

## 📝 Report Template

Copy and fill this after validation:

```
## Rich Features Validation Report

Date: ___________
ELO Group: mid (Gold/Platinum/Emerald)
Data Size: _____ matches

### Asset Building
- Matchups: [✅/❌] _____
- Embeddings: [✅/❌] _____
- Priors: [✅/❌] _____

### Model Training
- Feature Dims: _____ (target: 487)
- ROC-AUC: _____ (target: >0.58)
- Brier Score: _____ (target: <0.25)
- ECE: _____ (target: <0.05)
- Gate Status: [PASS/FAIL]

### UI Testing
- Confidence: _____% (target: 20-45%)
- Win Probabilities: _____% (target: varied, not 50%)
- Recommendation Win Gains: _____% (target: 1.5-5.5%)

### Status: [✅ READY / ⚠️ NEEDS WORK / ❌ FAILED]

### Next Steps:
- [ ] Collect more data (target: 3000+ matches)
- [ ] Retrain high ELO model
- [ ] Add patch 15.21 support
- [ ] Deploy to production
```

