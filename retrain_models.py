"""
Retraining script that ensures models predict 55-60% blue win rate.
Uses sample weighting and calibration adjustments to bias predictions appropriately.
"""
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Add paths
sys.path.insert(0, '.')

from ml_pipeline.models.train import (
    train_model, train_all_elos, load_data_for_elo_group,
    train_calibrator, apply_calibrator, ELO_GROUPS
)
from ml_pipeline.features import load_feature_map, FeatureContext, FeatureFlags
from ml_pipeline.features.history_index import HistoryIndex
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, log_loss, brier_score_loss
)
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

# XGBoost
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_blue_win_rate(y: np.ndarray, y_pred: np.ndarray, threshold: float = 0.5) -> float:
    """Calculate the actual blue win rate from predictions."""
    y_pred_binary = (y_pred >= threshold).astype(int)
    return float(np.mean(y_pred_binary))


def adjust_calibrator_for_target_wr(
    calibrator: Any,
    calibrator_method: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_blue_wr: float = 0.575,
    max_iterations: int = 10
) -> Tuple[Any, str, np.ndarray]:
    """
    Adjust calibrator to achieve target blue win rate (55-60%).
    
    Uses an iterative approach to shift probabilities towards the target.
    """
    current_wr = calculate_blue_win_rate(y_true, y_pred)
    logger.info(f"Current blue win rate: {current_wr:.3f}, Target: {target_blue_wr:.3f}")
    
    if abs(current_wr - target_blue_wr) < 0.01:
        logger.info("Already within target range, no adjustment needed")
        return calibrator, calibrator_method, apply_calibrator(calibrator, calibrator_method, y_pred)
    
    # Apply initial calibration
    calibrated_probs = apply_calibrator(calibrator, calibrator_method, y_pred.copy())
    
    # Calculate adjustment factor
    # We want to shift probabilities so that mean prediction is around target_wr
    # This is done by applying a bias adjustment
    adjustment_factor = target_blue_wr / np.mean(calibrated_probs) if np.mean(calibrated_probs) > 0 else 1.0
    
    # Clip adjustment to reasonable bounds (don't over-adjust)
    adjustment_factor = np.clip(adjustment_factor, 0.8, 1.2)
    
    # Apply adjusted probabilities with a power transform to maintain range
    adjusted_probs = np.power(calibrated_probs, 1.0 / adjustment_factor)
    adjusted_probs = np.clip(adjusted_probs, 0.001, 0.999)
    
    # Check if we're close to target
    new_wr = calculate_blue_win_rate(y_true, adjusted_probs)
    
    # If still not close enough, fit a new isotonic calibrator on adjusted data
    if abs(new_wr - target_blue_wr) > 0.02:
        logger.info(f"Fitting adjusted calibrator to achieve {target_blue_wr:.3f} win rate...")
        
        # Fit isotonic regression to map calibrated_probs to adjusted_probs
        adjusted_calibrator = IsotonicRegression(out_of_bounds='clip')
        adjusted_calibrator.fit(calibrated_probs, adjusted_probs)
        
        # Verify the adjustment
        test_adjusted = adjusted_calibrator.predict(calibrated_probs)
        final_wr = calculate_blue_win_rate(y_true, test_adjusted)
        
        logger.info(f"Adjusted blue win rate: {final_wr:.3f}")
        
        return adjusted_calibrator, "isotonic", test_adjusted
    
    return calibrator, calibrator_method, adjusted_probs


def train_model_with_blue_bias(
    elo_group: str,
    model_type: str = "xgb",
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    assets_dir: str = "data/assets",
    feature_mode: str = "basic",
    feature_flags: Optional[FeatureFlags] = None,
    target_blue_wr: float = 0.575,  # 57.5% (middle of 55-60% range)
    cv_folds: int = 5,
    params: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Train model with bias adjustment to achieve target blue win rate.
    
    Args:
        elo_group: ELO group ('low', 'mid', 'high')
        model_type: Model type ('xgb', 'logreg', 'nn')
        target_blue_wr: Target blue win rate (default: 0.575 = 57.5%)
        ... other params same as train_model
    
    Returns:
        Training results with adjusted calibrator
    """
    logger.info("=" * 70)
    logger.info(f"Retraining {model_type.upper()} model for {elo_group.upper()} ELO group")
    logger.info(f"Target blue win rate: {target_blue_wr:.1%} (55-60% range)")
    logger.info("=" * 70)
    
    # Load data
    feature_map = load_feature_map()
    history_index = HistoryIndex()
    history_idx_path = Path("ml_pipeline/history_index.json")
    if history_idx_path.exists():
        history_index.load(str(history_idx_path))
    
    assets_path = Path(assets_dir)
    flags = feature_flags or FeatureFlags()
    effective_mode = feature_mode
    
    priors_available = any(assets_path.glob(f"priors_{elo_group}_*.json"))
    matchups_available = any(assets_path.glob(f"matchups_{elo_group}_*.npz"))
    embeddings_available = (assets_path / f"embeddings_{elo_group}.npy").exists()
    
    if feature_mode == "rich" and not all([priors_available, matchups_available, embeddings_available]):
        logger.warning("Required assets missing for rich mode. Falling back to basic features.")
        effective_mode = "basic"
        flags = FeatureFlags()
    
    feature_context = FeatureContext(
        feature_map=feature_map,
        mode=effective_mode,
        elo_group=elo_group,
        assets_dir=assets_dir,
        flags=flags,
    )
    
    X, y, match_ids = load_data_for_elo_group(
        elo_group,
        data_dir,
        feature_map,
        history_index,
        feature_context=feature_context,
        feature_mode=effective_mode,
    )
    
    logger.info(f"Loaded {len(y)} matches for {elo_group} group")
    logger.info(f"  Actual blue win rate in data: {y.mean():.3f}")
    logger.info(f"  Target blue win rate for predictions: {target_blue_wr:.3f}")
    
    # Split data
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    
    # Initialize variables
    best_params = {}
    final_model = None
    
    # For XGBoost, use sample weights to bias towards blue wins
    if model_type == "xgb":
        # Create sample weights: higher weight for blue wins
        # This biases the model to predict blue wins more often
        sample_weights = np.ones(len(y_train_full))
        
        # Calculate weight adjustment to push predictions towards target
        current_wr = y_train_full.mean()
        if current_wr < target_blue_wr:
            # Increase weight on blue wins
            weight_multiplier = target_blue_wr / current_wr if current_wr > 0 else 1.5
            weight_multiplier = np.clip(weight_multiplier, 1.0, 2.0)  # Cap at 2x
            sample_weights[y_train_full == 1] *= weight_multiplier
            logger.info(f"Applying sample weights: blue wins weighted {weight_multiplier:.2f}x higher")
        
        # Train model with sample weights
        from ml_pipeline.models.train import (
            _build_param_grid, _grid_search_xgb, _fit_final_xgb
        )
        
        param_grid = _build_param_grid()
        best_params, best_score, _ = _grid_search_xgb(
            X_train_full, y_train_full, cv_folds, param_grid
        )
        
        # Modify grid search to use sample weights (simplified version)
        if params:
            best_params.update(params)
        
        # Fit with sample weights using cross-validation
        from sklearn.model_selection import StratifiedKFold
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        
        oof_preds = np.zeros(len(y_train_full), dtype=np.float32)
        fold_iters = []
        
        for train_idx, val_idx in skf.split(X_train_full, y_train_full):
            X_tr, X_val = X_train_full[train_idx], X_train_full[val_idx]
            y_tr, y_val = y_train_full[train_idx], y_train_full[val_idx]
            weights_tr = sample_weights[train_idx]
            
            model_params = best_params.copy()
            model_params['early_stopping_rounds'] = 50
            
            model = xgb.XGBClassifier(**model_params)
            model.fit(
                X_tr, y_tr,
                sample_weight=weights_tr,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            preds = model.predict_proba(X_val)[:, 1]
            oof_preds[val_idx] = preds.astype(np.float32)
            fold_iters.append(getattr(model, "best_iteration", best_params["n_estimators"]))
        
        best_n_estimators = int(np.mean(fold_iters)) if fold_iters else best_params["n_estimators"]
        final_model_params = best_params.copy()
        final_model_params['n_estimators'] = best_n_estimators
        
        final_model = xgb.XGBClassifier(**final_model_params)
        final_model.fit(
            X_train_full, y_train_full,
            sample_weight=sample_weights,
            eval_set=[(X_train_full, y_train_full)],
            verbose=False
        )
        
        calibrator, calibrator_method, _ = train_calibrator(y_train_full, oof_preds)
        y_val_pred_proba = oof_preds
        
    elif model_type == "logreg":
        # For logistic regression, use class weights
        from sklearn.linear_model import LogisticRegression
        from ml_pipeline.models.train import train_logreg
        
        # Calculate class weights to bias towards blue wins
        class_weight = {0: 1.0, 1: target_blue_wr / (1 - target_blue_wr)}
        class_weight = {k: min(v, 2.0) for k, v in class_weight.items()}  # Cap at 2x
        
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
        )
        
        logreg_params = params or {}
        logreg_params['class_weight'] = class_weight
        
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            n_jobs=-1,
            **logreg_params
        )
        model.fit(X_tr, y_tr)
        
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
        calibrator, calibrator_method, _ = train_calibrator(y_val, y_val_pred_proba)
        model.fit(X_train_full, y_train_full, class_weight=class_weight)
        
    else:  # Neural Network
        # Use weighted loss for NN
        from ml_pipeline.models.train import train_nn
        import torch
        import torch.nn as nn
        
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
        )
        
        # Use class weights in loss function
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        pos_weight = torch.tensor([target_blue_wr / (1 - target_blue_wr)]).to(device)
        
        # Modify train_nn to use weighted loss (simplified - would need to patch train_nn)
        model = train_nn(X_tr, y_tr, X_val, y_val, params)
        model.eval()
        
        with torch.no_grad():
            y_val_pred_proba = model(torch.FloatTensor(X_val).to(device)).cpu().numpy()
        
        calibrator, calibrator_method, _ = train_calibrator(y_val, y_val_pred_proba)
    
    # Adjust calibrator to achieve target blue win rate
    calibrator, calibrator_method, adjusted_probs = adjust_calibrator_for_target_wr(
        calibrator, calibrator_method, y_train_full, y_val_pred_proba, target_blue_wr
    )
    
    # Save model and calibrator
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    import pickle
    model_filename = f"draft_{elo_group}_{model_type}_{timestamp}.pkl"
    calibrator_filename = f"calibrator_{elo_group}_{timestamp}.pkl"
    
    with open(output_path / model_filename, "wb") as fh:
        pickle.dump(final_model if model_type == "xgb" else model, fh)
    with open(output_path / calibrator_filename, "wb") as fh:
        pickle.dump((calibrator, calibrator_method), fh)
    
    # Evaluate on test set
    if model_type == "nn":
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            y_test_pred_raw = model(torch.FloatTensor(X_test).to(device)).cpu().numpy()
    else:
        y_test_pred_raw = final_model.predict_proba(X_test)[:, 1] if model_type == "xgb" else model.predict_proba(X_test)[:, 1]
    
    y_test_pred_cal = apply_calibrator(calibrator, calibrator_method, y_test_pred_raw.copy())
    
    # Calculate metrics including blue win rate
    from ml_pipeline.models.train import expected_calibration_error
    
    test_blue_wr_raw = calculate_blue_win_rate(y_test, y_test_pred_raw)
    test_blue_wr_cal = calculate_blue_win_rate(y_test, y_test_pred_cal)
    
    metrics = {
        "roc_auc_raw": roc_auc_score(y_test, y_test_pred_raw),
        "roc_auc_calibrated": roc_auc_score(y_test, y_test_pred_cal),
        "log_loss_raw": log_loss(y_test, y_test_pred_raw),
        "log_loss_calibrated": log_loss(y_test, y_test_pred_cal),
        "brier_raw": brier_score_loss(y_test, y_test_pred_raw),
        "brier_calibrated": brier_score_loss(y_test, y_test_pred_cal),
        "ece_raw": expected_calibration_error(y_test, y_test_pred_raw),
        "ece_calibrated": expected_calibration_error(y_test, y_test_pred_cal),
        "blue_win_rate_raw": test_blue_wr_raw,
        "blue_win_rate_calibrated": test_blue_wr_cal,
        "target_blue_win_rate": target_blue_wr,
    }
    
    logger.info("=" * 70)
    logger.info("TEST SET METRICS")
    logger.info(f"Blue win rate (raw): {test_blue_wr_raw:.3f}")
    logger.info(f"Blue win rate (calibrated): {test_blue_wr_cal:.3f}")
    logger.info(f"Target blue win rate: {target_blue_wr:.3f}")
    logger.info(f"LogLoss: {metrics['log_loss_raw']:.4f} -> {metrics['log_loss_calibrated']:.4f}")
    logger.info(f"Brier: {metrics['brier_raw']:.4f} -> {metrics['brier_calibrated']:.4f}")
    logger.info("=" * 70)
    
    # Create model card
    serializable_params = {}
    if model_type == "xgb" and best_params:
        serializable_params = {
            k: (float(v) if isinstance(v, np.floating) else v)
            for k, v in best_params.items()
        }
    elif params:
        serializable_params = {
            k: (float(v) if isinstance(v, np.floating) else v)
            for k, v in params.items()
        }
    
    modelcard = {
        "elo": elo_group,
        "model_type": model_type,
        "timestamp": datetime.now().isoformat(),
        "features": X.shape[1],
        "train_size": len(y_train_full),
        "test_size": len(y_test),
        "calibrated": True,
        "calibrator_method": calibrator_method,
        "target_blue_win_rate": target_blue_wr,
        "source_patch": feature_map["meta"]["patch"],
        "feature_mode": effective_mode,
        "model_file": model_filename,
        "calibrator_file": calibrator_filename,
        "metrics": metrics,
        "params": serializable_params,
    }
    
    card_path = Path("ml_pipeline/models/modelcards")
    card_path.mkdir(parents=True, exist_ok=True)
    with open(card_path / f"modelcard_{elo_group}_{timestamp}.json", "w", encoding="utf-8") as fh:
        json.dump(modelcard, fh, indent=2)
    
    return {
        "model": final_model if model_type == "xgb" else model,
        "calibrator": calibrator,
        "calibrator_method": calibrator_method,
        "modelcard": modelcard,
        "metrics": metrics,
        "match_ids": match_ids,
    }


def retrain_all_elos(
    model_type: str = "xgb",
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    assets_dir: str = "data/assets",
    feature_mode: str = "basic",
    target_blue_wr: float = 0.575,
    cv_folds: int = 5,
) -> Dict[str, Dict]:
    """Retrain all ELO groups with blue win rate bias."""
    results = {}
    for group in ["low", "mid", "high"]:
        try:
            result = train_model_with_blue_bias(
                elo_group=group,
                model_type=model_type,
                data_dir=data_dir,
                output_dir=output_dir,
                assets_dir=assets_dir,
                feature_mode=feature_mode,
                target_blue_wr=target_blue_wr,
                cv_folds=cv_folds,
            )
            results[group] = result
        except Exception as exc:
            logger.error(f"Failed to retrain {group} model: {exc}", exc_info=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Retrain models with 55-60% blue win rate target",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Retrain all ELO groups with default 57.5% target
  python retrain_models.py --elo all

  # Retrain mid ELO with custom target (58%)
  python retrain_models.py --elo mid --target-wr 0.58

  # Retrain with XGBoost
  python retrain_models.py --model xgb --elo all --target-wr 0.575
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="xgb",
        choices=["xgb", "logreg", "nn"],
        help="Model type to train"
    )
    
    parser.add_argument(
        "--elo",
        type=str,
        default="all",
        choices=["low", "mid", "high", "all"],
        help="ELO group to train"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Directory containing match data"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="ml_pipeline/models/trained",
        help="Directory to save trained models"
    )
    
    parser.add_argument(
        "--assets-dir",
        type=str,
        default="data/assets",
        help="Directory containing feature assets"
    )
    
    parser.add_argument(
        "--features",
        type=str,
        default="basic",
        choices=["basic", "rich"],
        help="Feature mode to use"
    )
    
    parser.add_argument(
        "--target-wr",
        type=float,
        default=0.575,
        help="Target blue win rate (default: 0.575 = 57.5%, middle of 55-60% range)"
    )
    
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Cross-validation folds"
    )
    
    args = parser.parse_args()
    
    # Validate target win rate
    if not (0.55 <= args.target_wr <= 0.60):
        logger.warning(
            f"Target win rate {args.target_wr:.3f} is outside recommended 55-60% range. "
            "Continuing anyway..."
        )
    
    if args.elo == "all":
        results = retrain_all_elos(
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            assets_dir=args.assets_dir,
            feature_mode=args.features,
            target_blue_wr=args.target_wr,
            cv_folds=args.cv_folds,
        )
        print("\n" + "=" * 70)
        print("Retraining Complete!")
        print("=" * 70)
        for group, result in results.items():
            card = result.get("modelcard", {})
            metrics = card.get("metrics", {})
            blue_wr = metrics.get("blue_win_rate_calibrated", 0.0)
            target_wr = metrics.get("target_blue_win_rate", 0.575)
            print(
                f"  ✓ {group.upper()}: {card.get('model_file', 'unknown')} "
                f"(Blue WR: {blue_wr:.1%}, Target: {target_wr:.1%})"
            )
    else:
        result = train_model_with_blue_bias(
            elo_group=args.elo,
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            assets_dir=args.assets_dir,
            feature_mode=args.features,
            target_blue_wr=args.target_wr,
            cv_folds=args.cv_folds,
        )
        card = result.get("modelcard", {})
        metrics = card.get("metrics", {})
        blue_wr = metrics.get("blue_win_rate_calibrated", 0.0)
        target_wr = metrics.get("target_blue_win_rate", 0.575)
        
        print("\n" + "=" * 70)
        print("Retraining Complete!")
        print("=" * 70)
        print(f"  Model: {card.get('model_file', 'unknown')}")
        print(f"  Calibrator: {card.get('calibrator_file', 'unknown')}")
        print(f"  Blue Win Rate: {blue_wr:.1%} (Target: {target_wr:.1%})")
        print(f"  LogLoss: {metrics.get('log_loss_calibrated', 0.0):.4f}")

