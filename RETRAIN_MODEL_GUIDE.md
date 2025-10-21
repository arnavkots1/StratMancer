# 🎯 Model Retraining Guide - Fixing Overfitting

## 📊 **The Problem**

Your latest model (trained Oct 21) has:
- ❌ **ROC-AUC: 99.7%** (impossibly high - indicates severe overfitting)
- ❌ **3,410 features** with only ~1,000 training samples
- ❌ **Extreme predictions** (98% vs 2% on incomplete drafts)
- ❌ **Model memorized training data** instead of learning patterns

The older model (Oct 20) works better because it has:
- ✅ **3,309 features** (less overfitting)
- ✅ **More realistic predictions** (66% vs 34%)
- ✅ **Better generalization** to unseen drafts

## 🔧 **The Solution - Stronger Regularization**

I've updated the training configuration with **10x stronger regularization**:

### **Changes Made:**

1. **Reduced Model Complexity:**
   - `n_estimators`: 1500 → **500** (fewer trees)
   - `max_depth`: 6 → **4** (shallower trees)
   - `learning_rate`: 0.075 → **0.05** (slower learning)

2. **Increased Regularization:**
   - `reg_lambda`: 1.0 → **10.0** (10x stronger L2 regularization)
   - `reg_alpha`: 0 → **5.0** (NEW: L1 regularization for feature selection)
   - `gamma`: 0.0 → **0.5** (stronger tree pruning)
   - `min_child_weight`: 6 → **10** (require more samples per leaf)

3. **Data Subsampling:**
   - `subsample`: 0.8 → **0.7** (use 70% of data per tree)
   - `colsample_bytree`: 0.8 → **0.6** (use 60% of features per tree)

## 🚀 **How to Retrain**

### **Step 1: Retrain the Mid ELO Model**

```bash
python -m ml_pipeline.models.train --model xgb --elo mid --features rich --use-embeddings --use-matchups --use-synergy --ban-context
```

**Expected Training Time:** ~10-15 minutes

**What to Look For:**
- ✅ **ROC-AUC should be 0.55-0.65** (realistic for draft prediction)
- ✅ **Log Loss should be 0.65-0.69** (good calibration)
- ✅ **No warnings about overfitting**

### **Step 2: Retrain Low and High ELO Models**

```bash
# Low ELO (Bronze, Silver, Gold, Platinum)
python -m ml_pipeline.models.train --model xgb --elo low --features rich --use-embeddings --use-matchups --use-synergy --ban-context

# High ELO (Diamond+)
python -m ml_pipeline.models.train --model xgb --elo high --features rich --use-embeddings --use-matchups --use-synergy --ban-context
```

### **Step 3: Restart the Backend**

```bash
# Kill the current backend process (Ctrl+C)
python start_api.py
```

### **Step 4: Test in the UI**

1. Open http://localhost:3000/draft
2. Start a draft and make 5+ picks
3. Check predictions:
   - ✅ Should be **45-75% range** (not 5% or 95%)
   - ✅ Confidence should be **20-80%** (not 7% or 99%)
   - ✅ Predictions should change smoothly as you add picks

---

## 📈 **Expected Model Performance**

### **Realistic Metrics (after retraining):**

| Metric | Old (Overfitted) | New (Regularized) | What It Means |
|--------|------------------|-------------------|---------------|
| **ROC-AUC** | 0.997 ❌ | 0.55-0.65 ✅ | Ability to rank drafts by win probability |
| **Log Loss** | 0.06 | 0.65-0.69 ✅ | Calibration quality |
| **Brier Score** | 0.01 | 0.22-0.24 ✅ | Overall prediction accuracy |
| **ECE** | 0.02 | 0.05-0.08 ✅ | Calibration error |

**Why Lower is Better Now:**
- ROC-AUC > 0.95 = overfitted (memorizing, not learning)
- ROC-AUC 0.55-0.65 = realistic (learning patterns)

### **Prediction Examples:**

| Draft Stage | Old Model | New Model | Why New is Better |
|-------------|-----------|-----------|-------------------|
| 2 picks | 98% vs 2% ❌ | 52% vs 48% ✅ | Can't predict from 2 picks |
| 5 picks | 95% vs 5% ❌ | 58% vs 42% ✅ | More reasonable |
| 10 picks (complete) | 97% vs 3% ❌ | 64% vs 36% ✅ | Shows real advantage |

---

## ⚠️ **Important Notes**

### **1. More Features ≠ Better Model**

With 1,000 training samples:
- ❌ **3,410 features** = severe overfitting
- ✅ **3,410 features + strong regularization** = prevents overfitting

### **2. Low Confidence is OK**

- **7% confidence** on 2-3 picks = **correct** (model is uncertain)
- **95% confidence** on 2-3 picks = **wrong** (model is overconfident)

As you add more picks, confidence should **gradually increase**.

### **3. Need More Data for Best Results**

For truly strong models with 3,410 features:
- **Current:** ~1,000 matches per ELO
- **Better:** 5,000-10,000 matches per ELO
- **Ideal:** 50,000-100,000 matches per ELO

**How to Collect More Data:**

```bash
# Collect 2,000 matches per rank
python run_collector.py --ranks GOLD PLATINUM EMERALD --matches-per-rank 700

# This will give you ~2,100 matches for mid ELO
```

---

## 🎓 **Understanding the Metrics**

### **ROC-AUC (Receiver Operating Characteristic - Area Under Curve)**
- **What it measures:** Can the model correctly rank drafts by win probability?
- **Range:** 0.5 (random) to 1.0 (perfect)
- **For draft prediction:**
  - 0.50-0.55 = slightly better than random (good baseline)
  - 0.55-0.65 = decent predictive power (realistic target)
  - 0.65-0.75 = strong predictive power (excellent)
  - 0.90+ = **overfitted** (memorizing, not learning)

### **Log Loss (Cross-Entropy Loss)**
- **What it measures:** How well calibrated are the probabilities?
- **Range:** 0 (perfect) to ∞ (terrible)
- **For draft prediction:**
  - 0.69 = random guessing (baseline)
  - 0.65-0.68 = decent calibration
  - 0.60-0.65 = good calibration
  - < 0.10 = **likely overfitted**

### **Confidence (Model Uncertainty)**
- **What it measures:** `|probability - 0.5| * 200`
- **Examples:**
  - 50% vs 50% = 0% confidence (completely uncertain)
  - 60% vs 40% = 20% confidence (slight edge)
  - 70% vs 30% = 40% confidence (clear advantage)
  - 95% vs 5% = 90% confidence (overwhelming advantage - **suspicious**)

---

## 🔍 **Troubleshooting**

### **If Training Fails:**

1. **Check data exists:**
   ```bash
   dir data\processed
   ```
   Should see files like: `gold_15.20.json`, `platinum_15.20.json`, etc.

2. **Check feature assets exist:**
   ```bash
   dir ml_pipeline\feature_assets
   ```
   Should see: `champion_embeddings_mid_15.20.npy`, `matchup_map_mid_15.20.json`, etc.

3. **Rebuild feature assets if missing:**
   ```bash
   python -m ml_pipeline.features.build_assets --elo mid --patch 15.20 --embedding-dim 32 --min-samples 200
   ```

### **If Predictions Are Still Extreme:**

1. **Check which model is loaded:**
   - Look for `INFO:backend.services.inference:Model loaded for mid: xgb`
   - Should have timestamp matching your new training run

2. **Clear model cache:**
   - Restart the backend completely (Ctrl+C, then `python start_api.py`)

3. **Verify model metrics:**
   ```bash
   type ml_pipeline\models\modelcards\modelcard_mid_[latest_timestamp].json
   ```
   - ROC-AUC should be 0.55-0.65 (not 0.99)

---

## 📚 **Next Steps**

1. ✅ **Retrain with stronger regularization** (commands above)
2. ✅ **Test predictions in UI** (should be 45-75% range)
3. ✅ **Collect more data** (5,000+ matches per ELO for best results)
4. ✅ **Monitor model performance** (check metrics in model cards)

The key insight: **A model with realistic predictions that generalizes well is far better than an overfitted model with perfect training accuracy but terrible real-world performance.**


