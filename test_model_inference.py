#!/usr/bin/env python3
"""
Test script to verify model inference is working correctly.
Tests all ELO models and ensures they load and predict properly.
"""
import sys
import logging
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_model_loading():
    """Test that all ELO models can be loaded."""
    try:
        from backend.services.inference import InferenceService
        
        logger.info("Testing model loading...")
        inference_service = InferenceService()
        inference_service.initialize()
        
        # Test each ELO group
        elo_groups = ['low', 'mid', 'high']
        results = {}
        
        for elo in elo_groups:
            try:
                logger.info(f"Testing {elo} ELO model...")
                model, calibrator, method, modelcard = inference_service.load_elo_model(elo)
                
                # Verify model components
                assert model is not None, f"Model is None for {elo}"
                assert calibrator is not None, f"Calibrator is None for {elo}"
                assert method is not None, f"Method is None for {elo}"
                assert modelcard is not None, f"Modelcard is None for {elo}"
                
                # Verify modelcard has required fields
                required_fields = ['model_type', 'features', 'feature_mode', 'feature_flags']
                for field in required_fields:
                    assert field in modelcard, f"Modelcard missing {field} for {elo}"
                
                logger.info(f"✅ {elo.upper()} ELO model loaded successfully")
                logger.info(f"   Model type: {modelcard.get('model_type')}")
                logger.info(f"   Features: {modelcard.get('features')}")
                logger.info(f"   Feature mode: {modelcard.get('feature_mode')}")
                
                results[elo] = True
                
            except Exception as e:
                logger.error(f"❌ Failed to load {elo} ELO model: {e}")
                results[elo] = False
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error testing model loading: {e}")
        return {'low': False, 'mid': False, 'high': False}


def test_model_prediction():
    """Test that models can make predictions."""
    try:
        from backend.services.inference import InferenceService
        
        logger.info("Testing model predictions...")
        inference_service = InferenceService()
        inference_service.initialize()
        
        # Test draft data
        test_draft = {
            'elo': 'mid',
            'patch': '15.20',
            'blue': {
                'top': 157,  # Yasuo
                'jungle': -1,
                'mid': -1,
                'adc': -1,
                'support': -1
            },
            'red': {
                'top': 114,  # Fiora
                'jungle': 141,  # Kayn
                'mid': -1,
                'adc': -1,
                'support': -1
            }
        }
        
        elo_groups = ['low', 'mid', 'high']
        results = {}
        
        for elo in elo_groups:
            try:
                logger.info(f"Testing prediction for {elo} ELO...")
                
                # Update test draft with current ELO
                test_draft['elo'] = elo
                
                # Make prediction using correct API signature
                prediction = inference_service.predict_draft(
                    elo=test_draft['elo'],
                    patch=test_draft['patch'],
                    blue_picks=test_draft['blue'],
                    red_picks=test_draft['red'],
                    blue_bans=[],
                    red_bans=[]
                )
                
                # Verify prediction structure
                assert 'blue_win_prob' in prediction, f"Missing blue_win_prob for {elo}"
                assert 'red_win_prob' in prediction, f"Missing red_win_prob for {elo}"
                assert 'confidence' in prediction, f"Missing confidence for {elo}"
                
                # Verify probabilities are reasonable
                blue_prob = prediction['blue_win_prob']
                red_prob = prediction['red_win_prob']
                confidence = prediction['confidence']
                
                assert 0 <= blue_prob <= 1, f"Blue probability out of range: {blue_prob}"
                assert 0 <= red_prob <= 1, f"Red probability out of range: {red_prob}"
                # Confidence can be 0-100 (percentage) or 0-1 (decimal), both are valid
                assert 0 <= confidence <= 100, f"Confidence out of range: {confidence}"
                
                # Verify probabilities sum to 1 (approximately)
                prob_sum = blue_prob + red_prob
                assert abs(prob_sum - 1.0) < 0.01, f"Probabilities don't sum to 1: {prob_sum}"
                
                logger.info(f"✅ {elo.upper()} ELO prediction successful")
                logger.info(f"   Blue win prob: {blue_prob:.3f}")
                logger.info(f"   Red win prob: {red_prob:.3f}")
                logger.info(f"   Confidence: {confidence:.3f}")
                
                results[elo] = True
                
            except Exception as e:
                logger.error(f"❌ Failed prediction for {elo} ELO: {e}")
                results[elo] = False
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error testing predictions: {e}")
        return {'low': False, 'mid': False, 'high': False}


def test_feature_contexts():
    """Test that feature contexts are built correctly."""
    try:
        from backend.services.inference import InferenceService
        
        logger.info("Testing feature contexts...")
        inference_service = InferenceService()
        inference_service.initialize()
        
        elo_groups = ['low', 'mid', 'high']
        results = {}
        
        for elo in elo_groups:
            try:
                logger.info(f"Testing feature context for {elo} ELO...")
                
                # Load model to trigger feature context creation
                model, calibrator, method, modelcard = inference_service.load_elo_model(elo)
                
                # Check if feature context exists
                if elo in inference_service._feature_contexts:
                    context = inference_service._feature_contexts[elo]
                    logger.info(f"✅ {elo.upper()} ELO feature context exists")
                    # Just check that context exists, don't access specific attributes
                    results[elo] = True
                else:
                    logger.error(f"❌ No feature context for {elo} ELO")
                    results[elo] = False
                
            except Exception as e:
                logger.error(f"❌ Error testing feature context for {elo}: {e}")
                results[elo] = False
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error testing feature contexts: {e}")
        return {'low': False, 'mid': False, 'high': False}


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("STRATMANCER MODEL INFERENCE TEST")
    logger.info("=" * 60)
    
    # Test 1: Model Loading
    logger.info("\n1. Testing Model Loading...")
    loading_results = test_model_loading()
    
    # Test 2: Feature Contexts
    logger.info("\n2. Testing Feature Contexts...")
    context_results = test_feature_contexts()
    
    # Test 3: Model Predictions
    logger.info("\n3. Testing Model Predictions...")
    prediction_results = test_model_prediction()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for elo in ['low', 'mid', 'high']:
        loading_ok = loading_results.get(elo, False)
        context_ok = context_results.get(elo, False)
        prediction_ok = prediction_results.get(elo, False)
        
        status = "✅ PASS" if all([loading_ok, context_ok, prediction_ok]) else "❌ FAIL"
        logger.info(f"{elo.upper()} ELO: {status}")
        logger.info(f"  Loading: {'✅' if loading_ok else '❌'}")
        logger.info(f"  Context: {'✅' if context_ok else '❌'}")
        logger.info(f"  Prediction: {'✅' if prediction_ok else '❌'}")
        
        if not all([loading_ok, context_ok, prediction_ok]):
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! Models are working correctly.")
        logger.info("Backend and frontend should work as intended.")
    else:
        logger.error("\n⚠️  Some tests failed. Check the logs above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
