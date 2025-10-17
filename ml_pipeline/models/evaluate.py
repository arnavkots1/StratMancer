"""
Model evaluation with metrics, plots, and reports.
"""

import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    log_loss, brier_score_loss, confusion_matrix,
    roc_curve, precision_recall_curve
)

# calibration_curve moved in sklearn 1.0+
try:
    from sklearn.metrics import calibration_curve
except ImportError:
    from sklearn.calibration import calibration_curve

# For feature importance
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def predict_proba(model, X: np.ndarray, model_type: str) -> np.ndarray:
    """Get probability predictions from model."""
    if model_type == 'nn':
        model.eval()
        device = next(model.parameters()).device
        with torch.no_grad():
            probs = model(torch.FloatTensor(X).to(device)).cpu().numpy()
        return probs
    else:
        # XGBoost or LogReg
        return model.predict_proba(X)[:, 1]


def compute_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    y_pred_proba_calibrated: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Compute comprehensive metrics.
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities (uncalibrated)
        y_pred_proba_calibrated: Calibrated probabilities (optional)
    
    Returns:
        Dictionary of metrics
    """
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'f1_score': f1_score(y_true, y_pred),
        'roc_auc': roc_auc_score(y_true, y_pred_proba),
        'log_loss': log_loss(y_true, y_pred_proba),
        'brier_score': brier_score_loss(y_true, y_pred_proba)
    }
    
    if y_pred_proba_calibrated is not None:
        y_pred_calib = (y_pred_proba_calibrated >= 0.5).astype(int)
        metrics.update({
            'accuracy_calibrated': accuracy_score(y_true, y_pred_calib),
            'f1_score_calibrated': f1_score(y_true, y_pred_calib),
            'log_loss_calibrated': log_loss(y_true, y_pred_proba_calibrated),
            'brier_score_calibrated': brier_score_loss(y_true, y_pred_proba_calibrated)
        })
    
    return metrics


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    output_path: Path,
    title: str = "Confusion Matrix"
):
    """Plot and save confusion matrix."""
    y_pred = (y_pred_proba >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['Red Win', 'Blue Win'],
        yticklabels=['Red Win', 'Blue Win']
    )
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved confusion matrix to {output_path}")


def plot_roc_curve_fig(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    output_path: Path,
    title: str = "ROC Curve"
):
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, linewidth=2, label=f'AUC = {auc:.3f}')
    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved ROC curve to {output_path}")


def plot_calibration_curve_fig(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    y_pred_proba_calibrated: np.ndarray,
    output_path: Path,
    title: str = "Reliability Diagram"
):
    """Plot and save calibration curve comparing uncalibrated vs calibrated."""
    # Compute calibration curves
    prob_true_uncalib, prob_pred_uncalib = calibration_curve(
        y_true, y_pred_proba, n_bins=10, strategy='uniform'
    )
    
    prob_true_calib, prob_pred_calib = calibration_curve(
        y_true, y_pred_proba_calibrated, n_bins=10, strategy='uniform'
    )
    
    plt.figure(figsize=(10, 6))
    
    # Plot calibration curves
    plt.plot(prob_pred_uncalib, prob_true_uncalib, 
             marker='o', linewidth=2, label='Uncalibrated')
    plt.plot(prob_pred_calib, prob_true_calib, 
             marker='s', linewidth=2, label='Calibrated')
    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect Calibration')
    
    plt.xlabel('Predicted Probability')
    plt.ylabel('True Probability')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved calibration curve to {output_path}")


def plot_feature_importance(
    model: Any,
    model_type: str,
    output_path: Path,
    top_n: int = 20,
    title: str = "Top Feature Importances"
):
    """Plot and save feature importance."""
    if model_type == 'xgb' and HAS_XGB:
        # XGBoost feature importance
        importance = model.feature_importances_
        feature_names = [f"Feature {i}" for i in range(len(importance))]
        
        # Get top features
        indices = np.argsort(importance)[-top_n:]
        top_importance = importance[indices]
        top_names = [feature_names[i] for i in indices]
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(top_n), top_importance)
        plt.yticks(range(top_n), top_names)
        plt.xlabel('Importance')
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved feature importance to {output_path}")
    
    elif model_type == 'logreg':
        # Logistic regression coefficients
        coef = np.abs(model.coef_[0])
        feature_names = [f"Feature {i}" for i in range(len(coef))]
        
        indices = np.argsort(coef)[-top_n:]
        top_coef = coef[indices]
        top_names = [feature_names[i] for i in indices]
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(top_n), top_coef)
        plt.yticks(range(top_n), top_names)
        plt.xlabel('|Coefficient|')
        plt.title(title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved feature importance to {output_path}")
    
    else:
        logger.warning(f"Feature importance not supported for {model_type}")


def evaluate_model(
    model: Any,
    calibrator: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str,
    elo_group: str,
    output_dir: str = "ml_pipeline/models"
) -> Dict[str, Any]:
    """
    Comprehensive model evaluation.
    
    Args:
        model: Trained model
        calibrator: Trained calibrator
        X_test: Test features
        y_test: Test labels
        model_type: 'xgb', 'logreg', or 'nn'
        elo_group: 'low', 'mid', or 'high'
        output_dir: Directory to save outputs
    
    Returns:
        Dictionary with metrics and plot paths
    """
    logger.info("=" * 70)
    logger.info(f"Evaluating {model_type.upper()} model for {elo_group.upper()} ELO")
    logger.info("=" * 70)
    
    output_path = Path(output_dir)
    plots_path = output_path / "plots"
    plots_path.mkdir(parents=True, exist_ok=True)
    
    # Get predictions
    y_pred_proba = predict_proba(model, X_test, model_type)
    y_pred_proba_calibrated = calibrator.predict(y_pred_proba)
    
    # Compute metrics
    metrics = compute_metrics(y_test, y_pred_proba, y_pred_proba_calibrated)
    
    logger.info("Metrics (Uncalibrated):")
    logger.info(f"  Accuracy:     {metrics['accuracy']:.4f}")
    logger.info(f"  F1 Score:     {metrics['f1_score']:.4f}")
    logger.info(f"  ROC-AUC:      {metrics['roc_auc']:.4f}")
    logger.info(f"  Log Loss:     {metrics['log_loss']:.4f}")
    logger.info(f"  Brier Score:  {metrics['brier_score']:.4f}")
    
    logger.info("\nMetrics (Calibrated):")
    logger.info(f"  Accuracy:     {metrics['accuracy_calibrated']:.4f}")
    logger.info(f"  F1 Score:     {metrics['f1_score_calibrated']:.4f}")
    logger.info(f"  Log Loss:     {metrics['log_loss_calibrated']:.4f}")
    logger.info(f"  Brier Score:  {metrics['brier_score_calibrated']:.4f}")
    
    # Generate plots
    plot_paths = {}
    
    # Confusion matrix
    cm_path = plots_path / f"confusion_matrix_{elo_group}_{model_type}.png"
    plot_confusion_matrix(
        y_test, y_pred_proba_calibrated, cm_path,
        title=f"Confusion Matrix - {elo_group.upper()} ({model_type.upper()})"
    )
    plot_paths['confusion_matrix'] = str(cm_path)
    
    # ROC curve
    roc_path = plots_path / f"roc_curve_{elo_group}_{model_type}.png"
    plot_roc_curve_fig(
        y_test, y_pred_proba, roc_path,
        title=f"ROC Curve - {elo_group.upper()} ({model_type.upper()})"
    )
    plot_paths['roc_curve'] = str(roc_path)
    
    # Calibration curve
    calib_path = plots_path / f"calibration_curve_{elo_group}_{model_type}.png"
    plot_calibration_curve_fig(
        y_test, y_pred_proba, y_pred_proba_calibrated, calib_path,
        title=f"Reliability Diagram - {elo_group.upper()} ({model_type.upper()})"
    )
    plot_paths['calibration_curve'] = str(calib_path)
    
    # Feature importance
    fi_path = plots_path / f"feature_importance_{elo_group}_{model_type}.png"
    plot_feature_importance(
        model, model_type, fi_path,
        title=f"Feature Importance - {elo_group.upper()} ({model_type.upper()})"
    )
    plot_paths['feature_importance'] = str(fi_path)
    
    # Save metrics JSON
    metrics_path = output_path / f"metrics_{elo_group}_{model_type}.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            'elo_group': elo_group,
            'model_type': model_type,
            'metrics': metrics,
            'test_size': len(y_test),
            'plots': plot_paths
        }, f, indent=2)
    
    logger.info(f"\nSaved metrics to {metrics_path}")
    
    return {
        'metrics': metrics,
        'plots': plot_paths,
        'metrics_file': str(metrics_path)
    }


def generate_report(
    results: Dict[str, Dict],
    output_path: str = "ml_pipeline/models/metrics_report.md"
) -> None:
    """
    Generate markdown report from evaluation results.
    
    Args:
        results: Dictionary mapping elo_group -> evaluation results
        output_path: Path to save report
    """
    logger.info(f"Generating evaluation report...")
    
    lines = [
        "# StratMancer Model Evaluation Report\n",
        f"**Generated:** {Path(output_path).stat().st_mtime if Path(output_path).exists() else 'N/A'}\n",
        "\n## Summary\n",
    ]
    
    # Summary table
    lines.append("| ELO Group | Model | Accuracy | F1 Score | ROC-AUC | Log Loss | Brier Score |")
    lines.append("|-----------|-------|----------|----------|---------|----------|-------------|")
    
    for elo_group, result in results.items():
        metrics = result['metrics']
        model_type = result.get('model_type', 'xgb')
        
        lines.append(
            f"| {elo_group.upper()} | {model_type.upper()} | "
            f"{metrics['accuracy_calibrated']:.4f} | "
            f"{metrics['f1_score_calibrated']:.4f} | "
            f"{metrics['roc_auc']:.4f} | "
            f"{metrics['log_loss_calibrated']:.4f} | "
            f"{metrics['brier_score_calibrated']:.4f} |"
        )
    
    # Detailed sections
    for elo_group, result in results.items():
        metrics = result['metrics']
        plots = result.get('plots', {})
        model_type = result.get('model_type', 'xgb')
        
        lines.extend([
            f"\n## {elo_group.upper()} ELO Group\n",
            f"**Model Type:** {model_type.upper()}\n",
            "\n### Metrics\n",
            "#### Uncalibrated",
            f"- **Accuracy:** {metrics['accuracy']:.4f}",
            f"- **F1 Score:** {metrics['f1_score']:.4f}",
            f"- **ROC-AUC:** {metrics['roc_auc']:.4f}",
            f"- **Log Loss:** {metrics['log_loss']:.4f}",
            f"- **Brier Score:** {metrics['brier_score']:.4f}\n",
            "#### Calibrated",
            f"- **Accuracy:** {metrics['accuracy_calibrated']:.4f}",
            f"- **F1 Score:** {metrics['f1_score_calibrated']:.4f}",
            f"- **Log Loss:** {metrics['log_loss_calibrated']:.4f}",
            f"- **Brier Score:** {metrics['brier_score_calibrated']:.4f}\n",
            "\n### Plots\n"
        ])
        
        for plot_name, plot_path in plots.items():
            if Path(plot_path).exists():
                rel_path = Path(plot_path).relative_to(Path(output_path).parent)
                lines.append(f"![{plot_name}]({rel_path})\n")
    
    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Saved evaluation report to {output_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate trained models')
    parser.add_argument(
        '--elo',
        type=str,
        required=True,
        choices=['low', 'mid', 'high'],
        help='ELO group to evaluate'
    )
    parser.add_argument(
        '--model-type',
        type=str,
        default='xgb',
        choices=['xgb', 'logreg', 'nn'],
        help='Model type'
    )
    parser.add_argument(
        '--model-path',
        type=str,
        required=True,
        help='Path to trained model file'
    )
    parser.add_argument(
        '--calibrator-path',
        type=str,
        required=True,
        help='Path to calibrator file'
    )
    parser.add_argument(
        '--test-data',
        type=str,
        required=True,
        help='Path to test data (numpy .npz file with X_test and y_test)'
    )
    
    args = parser.parse_args()
    
    # Load model and calibrator
    with open(args.model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(args.calibrator_path, 'rb') as f:
        calibrator = pickle.load(f)
    
    # Load test data
    test_data = np.load(args.test_data)
    X_test = test_data['X_test']
    y_test = test_data['y_test']
    
    # Evaluate
    results = evaluate_model(
        model, calibrator, X_test, y_test,
        args.model_type, args.elo
    )
    
    print("\n" + "=" * 70)
    print("Evaluation Complete!")
    print("=" * 70)
    print(f"Metrics saved to: {results['metrics_file']}")
    print(f"Plots saved to:")
    for plot_name, plot_path in results['plots'].items():
        print(f"  - {plot_name}: {plot_path}")

