# StratMancer ML Models

Complete training, evaluation, and inference pipeline for League of Legends draft prediction.

## 🚀 Quick Start

### 1. Train a Model

```bash
# Train XGBoost for mid ELO (GOLD, PLATINUM, EMERALD)
python ml_pipeline/models/train.py --model xgb --elo mid

# Train all ELO groups
python ml_pipeline/models/train.py --model xgb --elo all

# Try different model types
python ml_pipeline/models/train.py --model logreg --elo high
python ml_pipeline/models/train.py --model nn --elo low
```

### 2. Make Predictions

```python
from ml_pipeline.models.predict import predict
from ml_pipeline.features import assemble_features, load_feature_map

# Load feature map
feature_map = load_feature_map()

# Assemble features from match
X, named = assemble_features(match, 'GOLD', feature_map)

# Predict
result = predict(X, elo_group='mid', include_explanations=True)

print(f"{result['prediction']}: {result['blue_win_prob']:.1%}")
```

## 📂 Directory Structure

```
ml_pipeline/models/
├── __init__.py           # Package exports
├── train.py              # Training pipeline
├── evaluate.py           # Metrics and plots
├── predict.py            # Inference API
├── trained/              # Saved models (.pkl)
├── plots/                # Visualizations (.png)
├── modelcards/           # Model metadata (.json)
└── metrics_*.json        # Evaluation metrics
```

## 🎯 ELO Groups

| Group | Ranks Included |
|-------|----------------|
| **Low** | IRON, BRONZE, SILVER |
| **Mid** | GOLD, PLATINUM, EMERALD |
| **High** | DIAMOND, MASTER, GRANDMASTER, CHALLENGER |

## 🤖 Model Types

### XGBoost (Default)
- **Fast**: ~1ms inference
- **Interpretable**: Feature importances
- **Accurate**: Best performance on structured data

```bash
python ml_pipeline/models/train.py --model xgb --elo mid
```

### Logistic Regression
- **Simple**: Linear baseline
- **Fast**: <0.5ms inference
- **Interpretable**: Coefficient weights

```bash
python ml_pipeline/models/train.py --model logreg --elo mid
```

### Neural Network
- **Deep Learning**: 3 hidden layers [512, 256, 128]
- **Flexible**: Can learn complex patterns
- **PyTorch**: GPU-accelerated training

```bash
python ml_pipeline/models/train.py --model nn --elo mid
```

## 📊 Metrics

All models report:
- **Accuracy**: Overall correctness
- **F1 Score**: Harmonic mean of precision/recall
- **ROC-AUC**: Area under ROC curve
- **Log Loss**: Cross-entropy loss
- **Brier Score**: Probability accuracy

**Both uncalibrated and calibrated metrics provided**

## 🎨 Visualizations

Automatically generated:
1. **Confusion Matrix** - Predicted vs actual
2. **ROC Curve** - TPR vs FPR
3. **Calibration Curve** - Reliability diagram
4. **Feature Importance** - Top 20 features

Saved to: `ml_pipeline/models/plots/`

## 🔧 Training Details

### Data Split
- **Train**: 80%
- **Validation**: 10% (for early stopping & calibration)
- **Test**: 10% (for final evaluation)

### Calibration
- **Method**: Isotonic Regression
- **Purpose**: Align predicted probabilities with true frequencies
- **Benefit**: Better win% estimates

### Early Stopping
- Monitors validation loss
- Stops when no improvement for N rounds
- Prevents overfitting

## 📦 Model Files

### Naming Convention
```
draft_{elo}_{model}_{timestamp}.pkl
calibrator_{elo}_{timestamp}.pkl
modelcard_{elo}_{timestamp}.json
```

### Example
```
draft_mid_xgb_20251017_153045.pkl
calibrator_mid_20251017_153045.pkl
modelcard_mid_20251017_153045.json
```

## 🔮 Inference API

### Single Prediction

```python
from ml_pipeline.models.predict import predict

result = predict(
    features=X,              # Feature vector from assemble_features()
    elo_group='mid',         # 'low', 'mid', or 'high'
    include_explanations=True
)

# Result structure:
{
    'blue_win_prob': 0.623,
    'red_win_prob': 0.377,
    'confidence': 0.842,
    'prediction': 'BLUE',
    'model_version': 'mid_xgb_20251017_153045',
    'explanations': [
        '+ Feature_1245: 0.342',
        '+ Feature_892: 0.215',
        '- Feature_44: -0.156'
    ]
}
```

### Batch Prediction

```python
from ml_pipeline.models.predict import batch_predict

predictions = batch_predict(
    features_list=[X1, X2, X3, ...],
    elo_group='mid'
)

# Returns list of prediction dicts
```

### Performance
- **Single**: <10ms (including model load from cache)
- **Batch (100)**: ~50ms total (~0.5ms each)

## 🧪 Evaluation

```python
from ml_pipeline.models.evaluate import evaluate_model, generate_report

# Evaluate model
results = evaluate_model(
    model=model,
    calibrator=calibrator,
    X_test=X_test,
    y_test=y_test,
    model_type='xgb',
    elo_group='mid'
)

# Generate report
generate_report(
    results={'mid': results},
    output_path='ml_pipeline/models/metrics_report.md'
)
```

## 🎓 Model Cards

Each model has metadata:
```json
{
  "elo": "mid",
  "model_type": "xgb",
  "timestamp": "2025-10-17T15:30:45",
  "features": 3309,
  "train_size": 80,
  "val_size": 10,
  "test_size": 10,
  "calibrated": true,
  "source_patch": "15.20",
  "feature_version": "v1",
  "model_file": "draft_mid_xgb_20251017_153045.pkl",
  "calibrator_file": "calibrator_mid_20251017_153045.pkl"
}
```

## 📈 Typical Performance

With 100+ matches per ELO:

| Metric | Expected Range |
|--------|----------------|
| Accuracy | 55-65% |
| F1 Score | 0.55-0.65 |
| ROC-AUC | 0.60-0.70 |
| Brier Score | 0.23-0.25 |

**Note**: Performance improves with more data. Collect 500+ matches per ELO for production.

## 🔄 Retraining Workflow

```bash
# 1. Collect new data
python run_collector.py --ranks GOLD PLATINUM EMERALD --matches-per-rank 200

# 2. Rebuild history index
python -c "from ml_pipeline.features.history_index import HistoryIndex; h = HistoryIndex(); h.build_index(); h.save()"

# 3. Retrain models
python ml_pipeline/models/train.py --model xgb --elo all

# 4. Evaluate
# (Automatically done during training)

# 5. Deploy new models
# (Copy from trained/ to production)
```

## 🛠️ Advanced Usage

### Custom Hyperparameters

```python
from ml_pipeline.models.train import train_model

result = train_model(
    elo_group='mid',
    model_type='xgb',
    params={
        'max_depth': 8,
        'learning_rate': 0.05,
        'n_estimators': 300
    }
)
```

### Cross-Validation

```python
result = train_model(
    elo_group='mid',
    model_type='xgb',
    cv_folds=5  # 5-fold stratified CV
)
```

### Feature Importance

```python
from ml_pipeline.models.evaluate import plot_feature_importance

plot_feature_importance(
    model=trained_model,
    model_type='xgb',
    output_path='plots/importance.png',
    top_n=30  # Show top 30 features
)
```

## 📚 API Reference

### train_model()
```python
def train_model(
    elo_group: str,          # 'low', 'mid', or 'high'
    model_type: str = 'xgb', # 'xgb', 'logreg', or 'nn'
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    cv_folds: int = 5,
    params: Optional[Dict] = None
) -> Dict[str, Any]
```

### evaluate_model()
```python
def evaluate_model(
    model: Any,
    calibrator: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str,
    elo_group: str,
    output_dir: str = "ml_pipeline/models"
) -> Dict[str, Any]
```

### predict()
```python
def predict(
    features: np.ndarray,
    elo_group: str,
    model_dir: str = "ml_pipeline/models/trained",
    include_explanations: bool = True
) -> Dict[str, Any]
```

### load_model()
```python
def load_model(
    elo_group: str,
    model_dir: str = "ml_pipeline/models/trained"
) -> Tuple[Any, Any, Dict]
```

## 🐛 Troubleshooting

### ImportError: No module named 'xgboost'
```bash
pip install xgboost
```

### No training data found
```bash
python run_collector.py --ranks GOLD --matches-per-rank 100
```

### Poor model performance
- Collect more data (500+ matches per ELO)
- Check class balance (should be ~50/50)
- Try different model types
- Adjust hyperparameters

### Calibration doesn't improve
- Need more validation data (collect more matches)
- Check if uncalibrated probabilities are reasonable
- May need different calibration method

## 💡 Tips

1. **Start with XGBoost** - Best default choice
2. **Collect more data** - More matches = better performance
3. **Monitor calibration** - Check reliability diagrams
4. **Use batch prediction** - Faster for multiple predictions
5. **Cache models** - `load_model()` automatically caches in memory
6. **Version control** - Keep old models for rollback
7. **Regular retraining** - Retrain every patch for meta changes

---

**StratMancer ML Models v1.0**  
Built with 🎯 for production-ready draft prediction

