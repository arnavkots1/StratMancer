"""
Training pipeline for draft prediction models.
Supports XGBoost, Logistic Regression, and Neural Networks.
"""

import argparse
import json
import logging
import pickle
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score, 
    log_loss, brier_score_loss
)
from tqdm import tqdm

# XGBoost
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logging.warning("XGBoost not installed. Install with: pip install xgboost")

# PyTorch for Neural Network
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("PyTorch not installed. Install with: pip install torch")

# Local imports
import sys
sys.path.insert(0, '.')
from ml_pipeline.features import assemble_features, load_feature_map, FeatureContext, FeatureFlags
from ml_pipeline.features.history_index import HistoryIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ELO groupings
ELO_GROUPS = {
    'low': ['IRON', 'BRONZE', 'SILVER'],
    'mid': ['GOLD', 'PLATINUM', 'EMERALD'],
    'high': ['DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
}


if HAS_TORCH:
    class SimpleNN(nn.Module):
        """Simple feed-forward neural network for draft prediction."""
        
        def __init__(self, input_dim: int, hidden_dims: List[int] = [512, 256, 128]):
            super(SimpleNN, self).__init__()
            
            layers = []
            prev_dim = input_dim
            
            for hidden_dim in hidden_dims:
                layers.extend([
                    nn.Linear(prev_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.3)
                ])
                prev_dim = hidden_dim
            
            # Output layer
            layers.append(nn.Linear(prev_dim, 1))
            layers.append(nn.Sigmoid())
            
            self.network = nn.Sequential(*layers)
        
        def forward(self, x):
            return self.network(x).squeeze()
else:
    # Dummy class when PyTorch is not available
    class SimpleNN:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyTorch not available. Install with: pip install torch")


def load_data_for_elo_group(
    elo_group: str,
    data_dir: str = "data/processed",
    feature_map: Optional[Dict] = None,
    history_index: Optional[HistoryIndex] = None,
    feature_context: Optional[FeatureContext] = None,
    feature_mode: str = "basic",
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load and assemble features for an ELO group.
    
    Args:
        elo_group: 'low', 'mid', or 'high'
        data_dir: Directory containing match data
        feature_map: Feature map (loaded if None)
        history_index: History index (loaded if None)
    
    Returns:
        X: Feature matrix
        y: Labels (1=blue win, 0=red win)
        match_ids: List of match IDs
    """
    data_path = Path(data_dir)
    
    # Load resources if not provided
    if feature_map is None:
        feature_map = load_feature_map()
    
    # Only load history_index for basic mode (not needed for rich mode)
    if history_index is None and feature_mode == "basic":
        history_index = HistoryIndex()
        history_idx_path = Path("ml_pipeline/history_index.json")
        if history_idx_path.exists():
            history_index.load(str(history_idx_path))
        else:
            logger.warning("No history index found, building from scratch...")
            history_index.build_index()
    elif feature_mode == "rich":
        # Explicitly set to None for rich mode to avoid loading
        history_index = None
    
    # Collect all matches for ELOs in this group
    elos = ELO_GROUPS[elo_group]
    X_list = []
    y_list = []
    match_ids = []
    
    for elo in elos:
        match_file = data_path / f"matches_{elo}.json"
        
        if not match_file.exists():
            logger.warning(f"No data found for {elo} at {match_file}")
            continue
        
        logger.info(f"Loading {elo} matches...")
        with open(match_file, 'r') as f:
            matches = json.load(f)
        
        for match in tqdm(matches, desc=f"Processing {elo}", leave=False):
            try:
                X_vec, named = assemble_features(
                    match,
                    elo,
                    feature_map,
                    history_index,
                    mode=feature_mode,
                    context=feature_context,
                )
                y = 1 if named['blue_win'] else 0
                
                X_list.append(X_vec)
                y_list.append(y)
                match_ids.append(named['match_id'])
            except Exception as e:
                logger.error(f"Failed to process match {match.get('match_id')}: {e}")
    
    if not X_list:
        raise ValueError(f"No data loaded for ELO group {elo_group}")
    
    X = np.vstack(X_list)
    y = np.array(y_list)
    
    logger.info(f"Loaded {len(y)} matches for {elo_group} group")
    logger.info(f"  Feature shape: {X.shape}")
    logger.info(f"  Blue win rate: {y.mean():.3f}")
    
    return X, y, match_ids


def train_xgboost(
    X_train: np.ndarray, 
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    params: Optional[Dict] = None
) -> Any:
    """Train XGBoost classifier."""
    if not HAS_XGB:
        raise ImportError("XGBoost not installed")
    
    default_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'early_stopping_rounds': 20,
        'verbosity': 0
    }
    
    if params:
        default_params.update(params)
    
    logger.info("Training XGBoost model...")
    
    model = xgb.XGBClassifier(**default_params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    logger.info(f"  Best iteration: {model.best_iteration}")
    logger.info(f"  Best score: {model.best_score:.4f}")
    
    return model


def train_logreg(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    params: Optional[Dict] = None
) -> Any:
    """Train Logistic Regression classifier."""
    default_params = {
        'max_iter': 1000,
        'random_state': 42,
        'n_jobs': -1,
        'C': 1.0
    }
    
    if params:
        default_params.update(params)
    
    logger.info("Training Logistic Regression model...")
    
    model = LogisticRegression(**default_params)
    model.fit(X_train, y_train)
    
    val_score = model.score(X_val, y_val)
    logger.info(f"  Validation accuracy: {val_score:.4f}")
    
    return model


def train_nn(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    params: Optional[Dict] = None
) -> Any:
    """Train Neural Network classifier."""
    if not HAS_TORCH:
        raise ImportError("PyTorch not installed")
    
    default_params = {
        'hidden_dims': [512, 256, 128],
        'lr': 0.001,
        'batch_size': 64,
        'epochs': 100,
        'patience': 10
    }
    
    if params:
        default_params.update(params)
    
    logger.info("Training Neural Network model...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"  Using device: {device}")
    
    # Create model
    model = SimpleNN(X_train.shape[1], default_params['hidden_dims'])
    model = model.to(device)
    
    # Create data loaders
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.FloatTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.FloatTensor(y_val)
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=default_params['batch_size'],
        shuffle=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=default_params['batch_size'],
        shuffle=False
    )
    
    # Training setup
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=default_params['lr'])
    
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(default_params['epochs']):
        # Training
        model.train()
        train_loss = 0.0
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"  Epoch {epoch+1}/{default_params['epochs']}: "
                       f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= default_params['patience']:
                logger.info(f"  Early stopping at epoch {epoch+1}")
                break
    
    # Load best model
    model.load_state_dict(best_model_state)
    logger.info(f"  Best validation loss: {best_val_loss:.4f}")
    
    return model


def train_calibrator(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    method: str = "auto",
):
    """Fit a probability calibrator using Platt scaling or isotonic regression."""
    if method == "auto":
        method = "isotonic" if len(y_true) >= 10_000 else "platt"

    logger.info("Training %s calibrator...", method)

    if method == "isotonic":
        calibrator = IsotonicRegression(out_of_bounds='clip')
        calibrator.fit(y_pred_proba, y_true)
        calibrated_probs = calibrator.predict(y_pred_proba)
    else:
        platt = LogisticRegression(max_iter=1000)
        platt.fit(y_pred_proba.reshape(-1, 1), y_true)
        calibrator = platt
        calibrated_probs = platt.predict_proba(y_pred_proba.reshape(-1, 1))[:, 1]

    uncalib_brier = brier_score_loss(y_true, y_pred_proba)
    calib_brier = brier_score_loss(y_true, calibrated_probs)
    logger.info(f"  Uncalibrated Brier score: {uncalib_brier:.4f}")
    logger.info(f"  Calibrated Brier score: {calib_brier:.4f}")
    logger.info(f"  Improvement: {(uncalib_brier - calib_brier):.4f}")

    return calibrator, method, calibrated_probs


def apply_calibrator(calibrator: Any, method: str, probs: np.ndarray) -> np.ndarray:
    if calibrator is None:
        return probs
    if method == "isotonic":
        return calibrator.predict(probs)
    return calibrator.predict_proba(probs.reshape(-1, 1))[:, 1]


def expected_calibration_error(
    y_true: np.ndarray,
    probs: np.ndarray,
    n_bins: int = 10,
) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(probs, bins) - 1
    bin_totals = np.zeros(n_bins, dtype=np.float64)
    bin_correct = np.zeros(n_bins, dtype=np.float64)
    bin_confidence = np.zeros(n_bins, dtype=np.float64)

    for idx in range(n_bins):
        mask = bin_ids == idx
        if not np.any(mask):
            continue
        bin_totals[idx] = np.sum(mask)
        bin_correct[idx] = np.sum(y_true[mask]) / bin_totals[idx]
        bin_confidence[idx] = np.mean(probs[mask])

    weights = bin_totals / np.maximum(1.0, np.sum(bin_totals))
    ece = np.sum(weights * np.abs(bin_correct - bin_confidence))
    return float(ece)


BASE_XGB_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "n_estimators": 500,  # REDUCED: Fewer trees to prevent overfitting
    "subsample": 0.7,  # REDUCED: Use less data per tree
    "colsample_bytree": 0.6,  # REDUCED: Use less features per tree
    "learning_rate": 0.05,  # REDUCED: Slower learning
    "max_depth": 4,  # REDUCED: Shallower trees
    "min_child_weight": 10,  # INCREASED: Require more samples per leaf
    "gamma": 0.5,  # INCREASED: Stronger pruning
    "reg_lambda": 10.0,  # INCREASED: L2 regularization (was 1.0, now 10x stronger)
    "reg_alpha": 5.0,  # NEW: L1 regularization for feature selection
    "random_state": 42,
    "verbosity": 0,
    "n_jobs": -1,
    "use_label_encoder": False,
}


def _build_param_grid() -> List[Dict[str, float]]:
    """Build grid with strong regularization to prevent overfitting."""
    grid = []
    # Focus on shallower trees and stronger regularization
    for combo in product(
        [3, 4, 5],  # max_depth: shallower trees
        [8, 10, 12],  # min_child_weight: more samples per leaf
        [0.6, 0.7],  # subsample: use less data
        [0.5, 0.6],  # colsample: use less features
        [0.03, 0.05]  # learning_rate: slower learning
    ):
        max_depth, min_child_weight, subsample, colsample, eta = combo
        grid.append(
            {
                "max_depth": max_depth,
                "min_child_weight": min_child_weight,
                "subsample": subsample,
                "colsample_bytree": colsample,
                "learning_rate": eta,
                "reg_lambda": 10.0,  # Strong L2 regularization
                "reg_alpha": 5.0,  # Strong L1 regularization
            }
        )
    max_combos = 60
    if len(grid) > max_combos:
        grid = grid[:max_combos]
    return grid


def _merge_params(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    merged.update(override)
    return merged


def _grid_search_xgb(
    X: np.ndarray,
    y: np.ndarray,
    cv_folds: int,
    param_grid: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], float, int]:
    if not HAS_XGB:
        raise ImportError("XGBoost not installed")

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    best_params: Optional[Dict[str, Any]] = None
    best_score = float("inf")
    best_iter = BASE_XGB_PARAMS["n_estimators"]

    for params in param_grid:
        fold_scores = []
        fold_iters = []
        merged_params = _merge_params(BASE_XGB_PARAMS, params)

        for train_idx, val_idx in skf.split(X, y):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]

            # Add early_stopping_rounds to params for newer XGBoost versions
            model_params = merged_params.copy()
            model_params['early_stopping_rounds'] = 50
            
            model = xgb.XGBClassifier(**model_params)
            model.fit(
                X_tr,
                y_tr,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )

            preds = model.predict_proba(X_val)[:, 1]
            fold_scores.append(log_loss(y_val, preds))
            fold_iters.append(getattr(model, "best_iteration", merged_params["n_estimators"]))

        mean_score = float(np.mean(fold_scores))
        if mean_score < best_score:
            best_score = mean_score
            best_params = merged_params
            best_iter = int(np.mean(fold_iters)) if fold_iters else merged_params["n_estimators"]

    if best_params is None:
        best_params = dict(BASE_XGB_PARAMS)

    return best_params, best_score, best_iter


def _fit_final_xgb(
    X: np.ndarray,
    y: np.ndarray,
    params: Dict[str, Any],
    cv_folds: int,
) -> Tuple[Any, np.ndarray, int]:
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(y), dtype=np.float32)
    fold_iters: List[int] = []

    for train_idx, val_idx in skf.split(X, y):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        # Add early_stopping_rounds to params for newer XGBoost versions
        model_params = params.copy()
        model_params['early_stopping_rounds'] = 50
        
        model = xgb.XGBClassifier(**model_params)
        model.fit(
            X_tr,
            y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        preds = model.predict_proba(X_val)[:, 1]
        oof_preds[val_idx] = preds.astype(np.float32)
        fold_iters.append(getattr(model, "best_iteration", params["n_estimators"]))

    best_n_estimators = int(np.mean(fold_iters)) if fold_iters else params["n_estimators"]
    final_model_params = params.copy()
    final_model_params['n_estimators'] = best_n_estimators
    final_model = xgb.XGBClassifier(**final_model_params)
    final_model.fit(X, y, eval_set=[(X, y)], verbose=False)

    return final_model, oof_preds, best_n_estimators


def train_model(
    elo_group: str,
    model_type: str = "xgb",
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    assets_dir: str = "data/assets",
    feature_mode: str = "basic",
    feature_flags: Optional[FeatureFlags] = None,
    cv_folds: int = 5,
    params: Optional[Dict] = None,
) -> Dict[str, Any]:
    logger.info("=" * 70)
    logger.info("Training %s model for %s ELO group", model_type.upper(), elo_group.upper())
    logger.info("=" * 70)

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

    assets_info = {
        "priors": priors_available,
        "matchups": matchups_available,
        "embeddings": embeddings_available,
    }

    if feature_mode == "rich" and not all(assets_info.values()):
        logger.warning("Required assets missing for rich mode (%s). Falling back to basic features.", assets_info)
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

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )

    logger.info(
        "Data split -> train folds: %d samples (blue WR %.3f), hold-out test: %d samples (blue WR %.3f)",
        len(y_train_full),
        y_train_full.mean(),
        len(y_test),
        y_test.mean(),
    )

    if model_type == "xgb":
        param_grid = _build_param_grid()
        best_params, best_score, _ = _grid_search_xgb(X_train_full, y_train_full, cv_folds, param_grid)
        logger.info("Best CV logloss: %.4f", best_score)

        if params:
            best_params.update(params)

        model, oof_preds, best_n_estimators = _fit_final_xgb(X_train_full, y_train_full, best_params, cv_folds)
        logger.info("Selected n_estimators from CV: %d", best_n_estimators)

        calibrator, calibrator_method, calibrated_oof = train_calibrator(y_train_full, oof_preds)
        y_val_pred_proba = oof_preds
    elif model_type == "logreg":
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
        )
        model = train_logreg(X_tr, y_tr, X_val, y_val, params)
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
        calibrator, calibrator_method, _ = train_calibrator(y_val, y_val_pred_proba)
        model.fit(X_train_full, y_train_full)
    elif model_type == "nn":
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
        )
        model = train_nn(X_tr, y_tr, X_val, y_val, params)
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            y_val_pred_proba = model(torch.FloatTensor(X_val).to(device)).cpu().numpy()
        calibrator, calibrator_method, _ = train_calibrator(y_val, y_val_pred_proba)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model_filename = f"draft_{elo_group}_{model_type}_{timestamp}.pkl"
    calibrator_filename = f"calibrator_{elo_group}_{timestamp}.pkl"

    with open(output_path / model_filename, "wb") as fh:
        pickle.dump(model, fh)
    with open(output_path / calibrator_filename, "wb") as fh:
        pickle.dump((calibrator, calibrator_method), fh)

    if model_type == "nn":
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            y_test_pred_raw = model(torch.FloatTensor(X_test).to(device)).cpu().numpy()
    else:
        y_test_pred_raw = model.predict_proba(X_test)[:, 1]

    y_test_pred_cal = apply_calibrator(calibrator, calibrator_method, y_test_pred_raw.copy())

    metrics = {
        "roc_auc_raw": roc_auc_score(y_test, y_test_pred_raw),
        "roc_auc_calibrated": roc_auc_score(y_test, y_test_pred_cal),
        "log_loss_raw": log_loss(y_test, y_test_pred_raw),
        "log_loss_calibrated": log_loss(y_test, y_test_pred_cal),
        "brier_raw": brier_score_loss(y_test, y_test_pred_raw),
        "brier_calibrated": brier_score_loss(y_test, y_test_pred_cal),
        "ece_raw": expected_calibration_error(y_test, y_test_pred_raw),
        "ece_calibrated": expected_calibration_error(y_test, y_test_pred_cal),
    }

    logger.info(
        "Hold-out metrics | LogLoss raw %.4f -> %.4f calibrated | Brier raw %.4f -> %.4f | ECE raw %.4f -> %.4f",
        metrics["log_loss_raw"],
        metrics["log_loss_calibrated"],
        metrics["brier_raw"],
        metrics["brier_calibrated"],
        metrics["ece_raw"],
        metrics["ece_calibrated"],
    )

    serializable_params = {k: (float(v) if isinstance(v, np.floating) else v) for k, v in (best_params.items() if model_type == "xgb" else (params or {}))}

    modelcard = {
        "elo": elo_group,
        "model_type": model_type,
        "timestamp": datetime.now().isoformat(),
        "features": X.shape[1],
        "train_size": len(y_train_full),
        "test_size": len(y_test),
        "calibrated": True,
        "calibrator_method": calibrator_method,
        "source_patch": feature_map["meta"]["patch"],
        "feature_mode": effective_mode,
        "feature_flags": flags.__dict__,
        "assets": assets_info,
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
        "model": model,
        "calibrator": calibrator,
        "calibrator_method": calibrator_method,
        "modelcard": modelcard,
        "metrics": metrics,
        "match_ids": match_ids,
    }


def train_all_elos(
    model_type: str = "xgb",
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    assets_dir: str = "data/assets",
    feature_mode: str = "basic",
    feature_flags: Optional[FeatureFlags] = None,
    cv_folds: int = 5,
) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for group in ["low", "mid", "high"]:
        try:
            flags_copy = FeatureFlags(**(feature_flags.__dict__ if feature_flags else {}))
            result = train_model(
                elo_group=group,
                model_type=model_type,
                data_dir=data_dir,
                output_dir=output_dir,
                assets_dir=assets_dir,
                feature_mode=feature_mode,
                feature_flags=flags_copy,
                cv_folds=cv_folds,
            )
            results[group] = result
        except Exception as exc:
            logger.error("Failed to train %s model: %s", group, exc, exc_info=True)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train draft prediction models")
    parser.add_argument("--model", type=str, default="xgb", choices=["xgb", "logreg", "nn"], help="Model type to train")
    parser.add_argument("--elo", type=str, default="all", choices=["low", "mid", "high", "all"], help="ELO group to train")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Directory containing match data")
    parser.add_argument("--output-dir", type=str, default="ml_pipeline/models/trained", help="Directory to save trained models")
    parser.add_argument("--assets-dir", type=str, default="data/assets", help="Directory containing feature assets")
    parser.add_argument("--features", type=str, default="basic", choices=["basic", "rich"], help="Feature mode to use")
    parser.add_argument("--use-embeddings", action="store_true", help="Include embedding features in rich mode")
    parser.add_argument("--use-matchups", action="store_true", help="Include lane matchup features in rich mode")
    parser.add_argument("--use-synergy", action="store_true", help="Include duo synergy features in rich mode")
    parser.add_argument("--ban-context", action="store_true", help="Enable ban impact context features")
    parser.add_argument("--pick-order", action="store_true", help="Include pick order context features when available")
    parser.add_argument("--cv-folds", type=int, default=5, help="Cross-validation folds")

    args = parser.parse_args()

    flags = FeatureFlags(
        use_embeddings=args.use_embeddings,
        use_matchups=args.use_matchups,
        use_synergy=args.use_synergy,
        ban_context=args.ban_context,
        pick_order=args.pick_order,
    )

    if args.features != "rich":
        flags = FeatureFlags()

    if args.elo == "all":
        results = train_all_elos(
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            assets_dir=args.assets_dir,
            feature_mode=args.features,
            feature_flags=flags,
            cv_folds=args.cv_folds,
        )
        print("\n" + "=" * 70)
        print("Training Complete!")
        print("=" * 70)
        for group, result in results.items():
            card = result.get("modelcard", {})
            print(f"  ✓ {group.upper()}: {card.get('model_file', 'unknown')} (ECE {card.get('metrics', {}).get('ece_calibrated', 0.0):.4f})")
    else:
        result = train_model(
            elo_group=args.elo,
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            assets_dir=args.assets_dir,
            feature_mode=args.features,
            feature_flags=flags,
            cv_folds=args.cv_folds,
        )
        card = result.get("modelcard", {})
        print("\n" + "=" * 70)
        print("Training Complete!")
        print("=" * 70)
        print(f"  Model: {card.get('model_file', 'unknown')}")
        print(f"  Calibrator: {card.get('calibrator_file', 'unknown')} [{card.get('calibrator_method', 'n/a')}]")

