#!/usr/bin/env python3
"""Test feature context and assembly"""

import sys
sys.path.insert(0, '.')

from backend.services.inference import inference_service
from ml_pipeline.features import load_feature_map, FeatureContext, FeatureFlags

# Initialize the service
inference_service.initialize()

# Load the mid ELO model to see what context it creates
model, calibrator, method, modelcard = inference_service.load_elo_model('mid')

print("Model card:")
print(f"  Feature mode: {modelcard.get('feature_mode')}")
print(f"  Feature flags: {modelcard.get('feature_flags')}")
print(f"  Expected features: {modelcard.get('features')}")

# Get the feature context
context = inference_service._get_feature_context('mid')
if context:
    print(f"\nFeature context:")
    print(f"  Mode: {context.mode}")
    print(f"  Flags: {context.flags.__dict__}")
    print(f"  ELO group: {context.elo_group}")
    print(f"  Assets dir: {context.assets_dir}")
else:
    print("\nNo feature context found!")

# Test a simple prediction
test_draft = {
    'blue_picks': [1, 2, 3, 4, 5],  # Simple test picks
    'red_picks': [6, 7, 8, 9, 10],
    'blue_bans': [11, 12, 13, 14, 15],
    'red_bans': [16, 17, 18, 19, 20]
}

try:
    result = inference_service.predict_draft(
        elo='mid',
        patch='15.20',
        blue_picks=test_draft['blue_picks'],
        red_picks=test_draft['red_picks'],
        blue_bans=test_draft['blue_bans'],
        red_bans=test_draft['red_bans'],
        calibrated_for_ui=False
    )
    print(f"\nTest prediction:")
    print(f"  Blue win prob: {result['blue_win_prob']:.4f}")
    print(f"  Raw prob: {result['blue_win_prob_raw']:.4f}")
    print(f"  Calibrated prob: {result['blue_win_prob_calibrated']:.4f}")
except Exception as e:
    print(f"\nPrediction failed: {e}")

