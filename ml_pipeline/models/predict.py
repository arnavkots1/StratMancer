"""
Inference API for draft prediction with calibrated probabilities.
"""

import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Cache for loaded models (cleared on reload)
_MODEL_CACHE: Dict[str, Tuple[Any, Any, str, Dict]] = {}


def clear_model_cache():
    """Clear the model cache to force reload of models."""
    global _MODEL_CACHE
    _MODEL_CACHE.clear()
    logger.info("Model cache cleared")


def entropy(probs: np.ndarray) -> float:
    """Calculate entropy of probability distribution."""
    p = np.clip(probs, 1e-10, 1 - 1e-10)  # Avoid log(0)
    return -np.sum(p * np.log2(p))


def load_model(elo_group: str, model_dir: str = "ml_pipeline/models/trained") -> Tuple[Any, Any, str, Dict]:
    """
    Load trained model and calibrator for an ELO group.
    
    Args:
        elo_group: 'low', 'mid', or 'high'
        model_dir: Directory containing trained models
    
    Returns:
        Tuple of (model, calibrator, modelcard)
    """
    cache_key = f"{elo_group}_{model_dir}"
    
    if cache_key in _MODEL_CACHE:
        logger.debug(f"Using cached model for {elo_group}")
        return _MODEL_CACHE[cache_key]
    
    model_path = Path(model_dir)
    modelcard_path = Path("ml_pipeline/models/modelcards")
    
    # Find latest model for this ELO
    model_files = list(model_path.glob(f"draft_{elo_group}_*.pkl"))
    
    if not model_files:
        raise FileNotFoundError(f"No model found for ELO group: {elo_group}")
    
    # Sort by timestamp (embedded in filename) - use the LATEST model
    sorted_models = sorted(model_files)
    latest_model = sorted_models[-1]
    logger.info(f"Loading latest model: {latest_model.name}")
    
    # Extract timestamp and model type from filename
    # Format: draft_{elo}_{model_type}_{date}_{time}.pkl
    # Example: draft_mid_xgb_20251018_131740.pkl
    parts = latest_model.stem.split('_')
    timestamp = f"{parts[-2]}_{parts[-1]}"  # date_time: 20251018_131740
    model_type = parts[-3]
    
    # Find corresponding calibrator
    calibrator_file = model_path / f"calibrator_{elo_group}_{timestamp}.pkl"
    
    if not calibrator_file.exists():
        raise FileNotFoundError(f"Calibrator not found: {calibrator_file}")
    
    # Load model
    logger.info(f"Loading model: {latest_model}")
    with open(latest_model, 'rb') as f:
        model = pickle.load(f)
    
    # Load calibrator
    logger.info(f"Loading calibrator: {calibrator_file}")
    with open(calibrator_file, 'rb') as f:
        calibrator_obj = pickle.load(f)

    # Load model card first
    modelcard_file = modelcard_path / f"modelcard_{elo_group}_{timestamp}.json"
    
    if modelcard_file.exists():
        with open(modelcard_file, 'r') as f:
            modelcard = json.load(f)
    else:
        logger.warning(f"Model card not found: {modelcard_file}")
        modelcard = {
            'elo': elo_group,
            'model_type': model_type,
            'timestamp': timestamp
        }

    # Now we can safely access modelcard
    calibrator_method = modelcard.get('calibrator_method', 'isotonic')
    if isinstance(calibrator_obj, tuple) and len(calibrator_obj) == 2:
        calibrator, calibrator_method = calibrator_obj
    else:
        calibrator = calibrator_obj
    
    # Cache the loaded model
    _MODEL_CACHE[cache_key] = (model, calibrator, calibrator_method, modelcard)
    
    return model, calibrator, calibrator_method, modelcard


def predict_proba(model: Any, X: np.ndarray, model_type: str) -> np.ndarray:
    """Get probability predictions from model."""
    if model_type == 'nn':
        if not HAS_TORCH:
            raise ImportError("PyTorch not installed")
        
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            probs = model(torch.FloatTensor(X).to(device)).cpu().numpy()
        
        # Ensure it's a 1D array
        if probs.ndim > 1:
            probs = probs.squeeze()
        
        return probs
    else:
        # XGBoost or LogReg
        return model.predict_proba(X)[:, 1]


def apply_calibrator(calibrator: Any, method: str, probs: np.ndarray) -> np.ndarray:
    if calibrator is None:
        return probs
    if method == 'isotonic':
        return calibrator.predict(probs)
    if hasattr(calibrator, 'predict_proba'):
        return calibrator.predict_proba(probs.reshape(-1, 1))[:, 1]
    return calibrator.predict(probs.reshape(-1, 1))


def predict_raw_and_calibrated(
    model: Any,
    calibrator: Any,
    calibrator_method: str,
    X: np.ndarray,
    model_type: str,
) -> Tuple[np.ndarray, np.ndarray]:
    raw = predict_proba(model, X, model_type)
    if raw.ndim > 1:
        raw = raw.squeeze()
    calibrated = apply_calibrator(calibrator, calibrator_method, raw.copy())
    return raw, calibrated


def explain_sample(
    X: np.ndarray,
    model: Any,
    model_type: str,
    feature_names: Optional[List[str]] = None,
    top_n: int = 3
) -> Dict[str, List[Dict]]:
    """
    Explain a single prediction with top contributing features.
    
    Args:
        X: Feature vector (1D array)
        model: Trained model
        model_type: 'xgb', 'logreg', or 'nn'
        feature_names: Names of features (optional)
        top_n: Number of top features to return
    
    Returns:
        Dictionary with 'positive' and 'negative' feature contributions
    """
    if X.ndim == 1:
        X = X.reshape(1, -1)
    
    n_features = X.shape[1]
    
    if feature_names is None:
        feature_names = [f"Feature_{i}" for i in range(n_features)]
    
    # Get feature contributions
    if model_type == 'xgb' and HAS_XGB:
        # Use TreeExplainer for XGBoost
        try:
            import shap
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            contributions = shap_values[0]
        except ImportError:
            # Fallback: use feature importances as proxy
            logger.warning("SHAP not available, using feature importance as proxy")
            importances = model.feature_importances_
            contributions = X[0] * importances
    
    elif model_type == 'logreg':
        # Logistic regression: feature * coefficient
        coef = model.coef_[0]
        contributions = X[0] * coef
    
    elif model_type == 'nn':
        # For NN, we can't easily get feature importance
        # Use gradient-based approximation
        logger.warning("Feature importance not fully supported for NN, returning approximate values")
        contributions = np.abs(X[0])
    
    else:
        contributions = np.zeros(n_features)
    
    # Sort by contribution magnitude
    indices = np.argsort(np.abs(contributions))[::-1]
    
    # Separate positive and negative contributions
    positive = []
    negative = []
    
    for idx in indices:
        contrib = contributions[idx]
        feature = feature_names[idx]
        value = X[0, idx]
        
        entry = {
            'feature': feature,
            'value': float(value),
            'contribution': float(contrib)
        }
        
        if contrib > 0:
            positive.append(entry)
        else:
            negative.append(entry)
        
        if len(positive) >= top_n and len(negative) >= top_n:
            break
    
    return {
        'positive': positive[:top_n],
        'negative': negative[:top_n]
    }


def predict(
    features: np.ndarray,
    elo_group: str,
    model_dir: str = "ml_pipeline/models/trained",
    include_explanations: bool = True
) -> Dict[str, Any]:
    """
    Make a prediction with calibrated probabilities.
    
    Args:
        features: Feature vector (1D or 2D array)
        elo_group: 'low', 'mid', or 'high'
        model_dir: Directory containing trained models
        include_explanations: Whether to include feature explanations
    
    Returns:
        Prediction dictionary with probabilities and metadata
    """
    # Ensure 2D array
    if features.ndim == 1:
        features = features.reshape(1, -1)
    
    # Load model
    model, calibrator, modelcard = load_model(elo_group, model_dir)
    model_type = modelcard.get('model_type', 'xgb')
    
    # Get uncalibrated probabilities
    y_pred_proba = predict_proba(model, features, model_type)
    
    # Apply calibration
    if isinstance(y_pred_proba, (list, np.ndarray)):
        if len(y_pred_proba) == 1:
            y_pred_proba = y_pred_proba[0]
        else:
            y_pred_proba = y_pred_proba
    
    y_pred_proba_calibrated = calibrator.predict(np.array([y_pred_proba]))[0]
    
    # Ensure probability is in [0, 1]
    y_pred_proba_calibrated = np.clip(y_pred_proba_calibrated, 0.0, 1.0)
    
    # Calculate confidence (inverse entropy)
    probs = np.array([1 - y_pred_proba_calibrated, y_pred_proba_calibrated])
    ent = entropy(probs)
    confidence = 1.0 - (ent / 1.0)  # Normalize by max entropy (log2(2) = 1)
    
    result = {
        'blue_win_prob': float(y_pred_proba_calibrated),
        'red_win_prob': float(1 - y_pred_proba_calibrated),
        'confidence': float(confidence),
        'prediction': 'BLUE' if y_pred_proba_calibrated >= 0.5 else 'RED',
        'model_version': f"{elo_group}_{model_type}_{modelcard.get('timestamp', 'unknown')}",
        'elo_group': elo_group,
        'model_type': model_type
    }
    
    # Add explanations if requested
    if include_explanations:
        explanations = explain_sample(features, model, model_type, top_n=3)
        
        # Format as human-readable strings
        explanation_strings = []
        
        for contrib in explanations['positive'][:3]:
            explanation_strings.append(
                f"+ {contrib['feature']}: {contrib['contribution']:.3f}"
            )
        
        for contrib in explanations['negative'][:3]:
            explanation_strings.append(
                f"- {contrib['feature']}: {contrib['contribution']:.3f}"
            )
        
        result['explanations'] = explanation_strings
        result['detailed_explanations'] = explanations
    
    return result


def batch_predict(
    features_list: List[np.ndarray],
    elo_group: str,
    model_dir: str = "ml_pipeline/models/trained"
) -> List[Dict[str, Any]]:
    """
    Make predictions for multiple feature vectors.
    
    Args:
        features_list: List of feature vectors
        elo_group: 'low', 'mid', or 'high'
        model_dir: Directory containing trained models
    
    Returns:
        List of prediction dictionaries
    """
    # Load model once
    model, calibrator, modelcard = load_model(elo_group, model_dir)
    model_type = modelcard.get('model_type', 'xgb')
    
    # Stack features
    X = np.vstack(features_list)
    
    # Get predictions
    y_pred_proba = predict_proba(model, X, model_type)
    y_pred_proba_calibrated = calibrator.predict(y_pred_proba)
    
    # Format results
    results = []
    for i, prob in enumerate(y_pred_proba_calibrated):
        prob = np.clip(prob, 0.0, 1.0)
        probs = np.array([1 - prob, prob])
        ent = entropy(probs)
        confidence = 1.0 - ent
        
        results.append({
            'blue_win_prob': float(prob),
            'red_win_prob': float(1 - prob),
            'confidence': float(confidence),
            'prediction': 'BLUE' if prob >= 0.5 else 'RED',
            'model_version': f"{elo_group}_{model_type}_{modelcard.get('timestamp', 'unknown')}"
        })
    
    return results


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == '__main__':
    import argparse
    import sys
    sys.path.insert(0, '.')
    
    from ml_pipeline.features import assemble_features, load_feature_map
    from ml_pipeline.features.history_index import HistoryIndex
    
    parser = argparse.ArgumentParser(description='Make draft predictions')
    parser.add_argument(
        '--match-file',
        type=str,
        required=True,
        help='Path to match JSON file'
    )
    parser.add_argument(
        '--elo',
        type=str,
        required=True,
        choices=['low', 'mid', 'high'],
        help='ELO group'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='ml_pipeline/models/trained',
        help='Directory containing trained models'
    )
    
    args = parser.parse_args()
    
    # Load match
    with open(args.match_file, 'r') as f:
        match = json.load(f)
    
    # Assemble features
    logger.info("Assembling features...")
    feature_map = load_feature_map()
    history_index = HistoryIndex()
    
    history_idx_path = Path("ml_pipeline/history_index.json")
    if history_idx_path.exists():
        history_index.load(str(history_idx_path))
    
    X, named = assemble_features(match, 'GOLD', feature_map, history_index)
    
    # Make prediction
    logger.info("Making prediction...")
    result = predict(X, args.elo, args.model_dir)
    
    # Print result
    print("\n" + "=" * 70)
    print("Draft Prediction")
    print("=" * 70)
    print(f"Match ID: {named['match_id']}")
    print(f"Blue picks: {named['blue_picks']}")
    print(f"Red picks: {named['red_picks']}")
    print()
    print(f"Prediction: {result['prediction']}")
    print(f"Blue win probability: {result['blue_win_prob']:.2%}")
    print(f"Red win probability: {result['red_win_prob']:.2%}")
    print(f"Confidence: {result['confidence']:.2%}")
    print()
    print("Top feature contributions:")
    for explanation in result.get('explanations', []):
        print(f"  {explanation}")
    print()
    print(f"Model: {result['model_version']}")
    print("=" * 70)
    
    # Print JSON output
    print("\nJSON Output:")
    print(json.dumps(result, indent=2))
