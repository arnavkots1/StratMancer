"""
API tests for prediction endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.main import app

client = TestClient(app)

# Test data
VALID_PREDICT_REQUEST = {
    "elo": "mid",
    "patch": "15.20",
    "blue": {
        "top": 1,
        "jungle": 2,
        "mid": 3,
        "adc": 4,
        "support": 5,
        "bans": [6, 7, 8, 9, 10]
    },
    "red": {
        "top": 11,
        "jungle": 12,
        "mid": 13,
        "adc": 14,
        "support": 15,
        "bans": [16, 17, 18, 19, 20]
    }
}

INVALID_PREDICT_REQUEST = {
    "elo": "invalid",
    "patch": "15.20",
    "blue": {
        "top": 1,
        "jungle": 2,
        "mid": 3,
        "adc": 4,
        "support": 5,
        "bans": [6, 7, 8, 9, 10]
    },
    "red": {
        "top": 11,
        "jungle": 12,
        "mid": 13,
        "adc": 14,
        "support": 15,
        "bans": [16, 17, 18, 19, 20]
    }
}

MISSING_ROLES_REQUEST = {
    "elo": "mid",
    "patch": "15.20",
    "blue": {
        "top": 1,
        "jungle": 2,
        "mid": 3,
        "adc": 4,
        "bans": [6, 7, 8, 9, 10]
    },
    "red": {
        "top": 11,
        "jungle": 12,
        "mid": 13,
        "adc": 14,
        "support": 15,
        "bans": [16, 17, 18, 19, 20]
    }
}


class TestPredictAPI:
    """Test prediction API endpoints"""
    
    def test_predict_draft_valid_request(self):
        """Test valid prediction request returns 200 with probabilities"""
        with patch('backend.services.inference.InferenceService.predict_draft') as mock_predict:
            mock_predict.return_value = {
                'blue_win_prob': 0.65,
                'red_win_prob': 0.35,
                'confidence': 0.85,
                'calibrated': True,
                'explanations': ['+Strong engage', '+AP balance'],
                'model_version': 'mid-xgb-2025-10-18',
                'elo_group': 'mid',
                'patch': '15.20'
            }
            
            response = client.post(
                "/predict-draft",
                json=VALID_PREDICT_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "blue_win_prob" in data
            assert "red_win_prob" in data
            assert "confidence" in data
            assert data["blue_win_prob"] == 0.65
            assert data["red_win_prob"] == 0.35
    
    def test_predict_draft_invalid_elo(self):
        """Test prediction with invalid ELO returns 422"""
        response = client.post(
            "/predict-draft",
            json=INVALID_PREDICT_REQUEST,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_predict_draft_missing_roles(self):
        """Test prediction with missing roles returns 422"""
        response = client.post(
            "/predict-draft",
            json=MISSING_ROLES_REQUEST,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_predict_draft_missing_api_key(self):
        """Test prediction without API key returns 401"""
        response = client.post(
            "/predict-draft",
            json=VALID_PREDICT_REQUEST
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "API key" in data["detail"]
    
    def test_predict_draft_invalid_api_key(self):
        """Test prediction with invalid API key returns 401"""
        response = client.post(
            "/predict-draft",
            json=VALID_PREDICT_REQUEST,
            headers={"X-STRATMANCER-KEY": "invalid-key"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "API key" in data["detail"]
    
    def test_predict_draft_oversized_payload(self):
        """Test prediction with oversized payload returns 413"""
        # Create a large payload (over 32KB)
        large_bans = list(range(1, 1000))  # Large list to exceed 32KB
        large_request = VALID_PREDICT_REQUEST.copy()
        large_request["blue"]["bans"] = large_bans
        large_request["red"]["bans"] = large_bans
        
        response = client.post(
            "/predict-draft",
            json=large_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "detail" in data
        assert "payload" in data["detail"].lower()
    
    def test_predict_draft_invalid_champion_id(self):
        """Test prediction with invalid champion ID returns 400"""
        invalid_request = VALID_PREDICT_REQUEST.copy()
        invalid_request["blue"]["top"] = 99999  # Invalid champion ID
        
        response = client.post(
            "/predict-draft",
            json=invalid_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "champion" in data["detail"].lower()
    
    def test_predict_draft_duplicate_bans(self):
        """Test prediction with duplicate bans is handled gracefully"""
        duplicate_request = VALID_PREDICT_REQUEST.copy()
        duplicate_request["blue"]["bans"] = [1, 1, 2, 2, 3]  # Duplicates
        duplicate_request["red"]["bans"] = [4, 4, 5, 5, 6]  # Duplicates
        
        with patch('backend.services.inference.InferenceService.predict_draft') as mock_predict:
            mock_predict.return_value = {
                'blue_win_prob': 0.5,
                'red_win_prob': 0.5,
                'confidence': 0.5,
                'calibrated': True,
                'explanations': [],
                'model_version': 'mid-xgb-2025-10-18',
                'elo_group': 'mid',
                'patch': '15.20'
            }
            
            response = client.post(
                "/predict-draft",
                json=duplicate_request,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            # Should succeed (duplicates are deduplicated automatically)
            assert response.status_code == 200
    
    def test_predict_draft_model_not_available(self):
        """Test prediction when model is not available returns 503"""
        with patch('backend.services.inference.InferenceService.predict_draft') as mock_predict:
            mock_predict.side_effect = ValueError("No model available for ELO group: invalid")
            
            response = client.post(
                "/predict-draft",
                json=INVALID_PREDICT_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "model" in data["detail"].lower()
    
    def test_predict_draft_internal_error(self):
        """Test prediction with internal error returns 500"""
        with patch('backend.services.inference.InferenceService.predict_draft') as mock_predict:
            mock_predict.side_effect = Exception("Internal error")
            
            response = client.post(
                "/predict-draft",
                json=VALID_PREDICT_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "error" in data or "unexpected" in data["detail"].lower()
    
    def test_predict_draft_response_headers(self):
        """Test prediction response includes proper headers"""
        with patch('backend.services.inference.InferenceService.predict_draft') as mock_predict:
            mock_predict.return_value = {
                'blue_win_prob': 0.65,
                'red_win_prob': 0.35,
                'confidence': 0.85,
                'calibrated': True,
                'explanations': ['+Strong engage'],
                'model_version': 'mid-xgb-2025-10-18',
                'elo_group': 'mid',
                'patch': '15.20'
            }
            
            response = client.post(
                "/predict-draft",
                json=VALID_PREDICT_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            assert "content-type" in response.headers
            assert response.headers["content-type"] == "application/json"
