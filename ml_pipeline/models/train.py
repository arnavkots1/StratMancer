"""
Training pipeline for draft prediction models.
Supports XGBoost, Logistic Regression, and Neural Networks.
"""

import json
import pickle
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

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
from ml_pipeline.features import assemble_features, load_feature_map
from ml_pipeline.features.history_index import HistoryIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ELO groupings
ELO_GROUPS = {
    'low': ['IRON', 'BRONZE', 'SILVER'],
    'mid': ['GOLD', 'PLATINUM', 'EMERALD'],
    'high': ['DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
}


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


def load_data_for_elo_group(
    elo_group: str,
    data_dir: str = "data/processed",
    feature_map: Optional[Dict] = None,
    history_index: Optional[HistoryIndex] = None
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
    
    if history_index is None:
        history_index = HistoryIndex()
        history_idx_path = Path("ml_pipeline/history_index.json")
        if history_idx_path.exists():
            history_index.load(str(history_idx_path))
        else:
            logger.warning("No history index found, building from scratch...")
            history_index.build_index()
    
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
                X_vec, named = assemble_features(match, elo, feature_map, history_index)
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


def calibrate_probabilities(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray
) -> IsotonicRegression:
    """
    Train isotonic regression calibrator.
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities
    
    Returns:
        Trained calibrator
    """
    logger.info("Training probability calibrator...")
    
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(y_pred_proba, y_true)
    
    # Evaluate calibration improvement
    calibrated_probs = calibrator.predict(y_pred_proba)
    
    uncalib_brier = brier_score_loss(y_true, y_pred_proba)
    calib_brier = brier_score_loss(y_true, calibrated_probs)
    
    logger.info(f"  Uncalibrated Brier score: {uncalib_brier:.4f}")
    logger.info(f"  Calibrated Brier score: {calib_brier:.4f}")
    logger.info(f"  Improvement: {(uncalib_brier - calib_brier):.4f}")
    
    return calibrator


def train_model(
    elo_group: str,
    model_type: str = 'xgb',
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained",
    cv_folds: int = 5,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Train a model for an ELO group.
    
    Args:
        elo_group: 'low', 'mid', or 'high'
        model_type: 'xgb', 'logreg', or 'nn'
        data_dir: Directory containing match data
        output_dir: Directory to save trained models
        cv_folds: Number of cross-validation folds
        params: Model-specific parameters
    
    Returns:
        Dictionary with training results and metadata
    """
    logger.info("=" * 70)
    logger.info(f"Training {model_type.upper()} model for {elo_group.upper()} ELO group")
    logger.info("=" * 70)
    
    # Load data
    feature_map = load_feature_map()
    history_index = HistoryIndex()
    
    history_idx_path = Path("ml_pipeline/history_index.json")
    if history_idx_path.exists():
        history_index.load(str(history_idx_path))
    
    X, y, match_ids = load_data_for_elo_group(
        elo_group, data_dir, feature_map, history_index
    )
    
    # Split data: 80% train, 10% val, 10% test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.111, random_state=42, stratify=y_temp  # 0.111 of 90% = 10% of total
    )
    
    logger.info(f"Data split:")
    logger.info(f"  Train: {len(y_train)} samples ({y_train.mean():.3f} blue WR)")
    logger.info(f"  Val:   {len(y_val)} samples ({y_val.mean():.3f} blue WR)")
    logger.info(f"  Test:  {len(y_test)} samples ({y_test.mean():.3f} blue WR)")
    
    # Train model
    if model_type == 'xgb':
        model = train_xgboost(X_train, y_train, X_val, y_val, params)
    elif model_type == 'logreg':
        model = train_logreg(X_train, y_train, X_val, y_val, params)
    elif model_type == 'nn':
        model = train_nn(X_train, y_train, X_val, y_val, params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Get validation predictions for calibration
    if model_type == 'nn':
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            y_val_pred_proba = model(torch.FloatTensor(X_val).to(device)).cpu().numpy()
    elif model_type == 'xgb':
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
    else:  # logreg
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
    
    # Train calibrator
    calibrator = calibrate_probabilities(y_val, y_val_pred_proba)
    
    # Save model and calibrator
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_filename = f"draft_{elo_group}_{model_type}_{timestamp}.pkl"
    calibrator_filename = f"calibrator_{elo_group}_{timestamp}.pkl"
    
    model_path = output_path / model_filename
    calibrator_path = output_path / calibrator_filename
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(calibrator_path, 'wb') as f:
        pickle.dump(calibrator, f)
    
    logger.info(f"Saved model to: {model_path}")
    logger.info(f"Saved calibrator to: {calibrator_path}")
    
    # Create model card
    modelcard = {
        'elo': elo_group,
        'model_type': model_type,
        'timestamp': datetime.now().isoformat(),
        'features': X.shape[1],
        'train_size': len(y_train),
        'val_size': len(y_val),
        'test_size': len(y_test),
        'calibrated': True,
        'source_patch': feature_map['meta']['patch'],
        'feature_version': 'v1',
        'model_file': model_filename,
        'calibrator_file': calibrator_filename
    }
    
    modelcard_path = Path("ml_pipeline/models/modelcards") / f"modelcard_{elo_group}_{timestamp}.json"
    modelcard_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(modelcard_path, 'w') as f:
        json.dump(modelcard, f, indent=2)
    
    logger.info(f"Saved model card to: {modelcard_path}")
    
    return {
        'model': model,
        'calibrator': calibrator,
        'modelcard': modelcard,
        'X_train': X_train,
        'y_train': y_train,
        'X_val': X_val,
        'y_val': y_val,
        'X_test': X_test,
        'y_test': y_test
    }


def train_all_elos(
    model_type: str = 'xgb',
    data_dir: str = "data/processed",
    output_dir: str = "ml_pipeline/models/trained"
) -> Dict[str, Dict]:
    """
    Train models for all ELO groups.
    
    Args:
        model_type: 'xgb', 'logreg', or 'nn'
        data_dir: Directory containing match data
        output_dir: Directory to save trained models
    
    Returns:
        Dictionary mapping elo_group -> training results
    """
    results = {}
    
    for elo_group in ['low', 'mid', 'high']:
        try:
            result = train_model(
                elo_group=elo_group,
                model_type=model_type,
                data_dir=data_dir,
                output_dir=output_dir
            )
            results[elo_group] = result
        except Exception as e:
            logger.error(f"Failed to train {elo_group} model: {e}")
            import traceback
            traceback.print_exc()
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Train draft prediction models'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='xgb',
        choices=['xgb', 'logreg', 'nn'],
        help='Model type to train'
    )
    parser.add_argument(
        '--elo',
        type=str,
        default='all',
        choices=['low', 'mid', 'high', 'all'],
        help='ELO group to train (default: all)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/processed',
        help='Directory containing match data'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='ml_pipeline/models/trained',
        help='Directory to save trained models'
    )
    
    args = parser.parse_args()
    
    if args.elo == 'all':
        results = train_all_elos(
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir
        )
        
        print("\n" + "=" * 70)
        print("Training Complete!")
        print("=" * 70)
        print(f"Trained {len(results)} models:")
        for elo_group, result in results.items():
            print(f"  ✓ {elo_group.upper()}: {result['modelcard']['model_file']}")
    else:
        result = train_model(
            elo_group=args.elo,
            model_type=args.model,
            data_dir=args.data_dir,
            output_dir=args.output_dir
        )
        
        print("\n" + "=" * 70)
        print("Training Complete!")
        print("=" * 70)
        print(f"  Model: {result['modelcard']['model_file']}")
        print(f"  Calibrator: {result['modelcard']['calibrator_file']}")

