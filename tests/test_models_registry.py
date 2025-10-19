"""
Model registry tests
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.main import app

client = TestClient(app)


class TestModelsRegistry:
    """Test model registry endpoints"""
    
    def test_get_models_registry(self):
        """Test GET /models/registry returns model cards"""
        with patch('backend.services.model_registry.ModelRegistry.get_all_modelcards') as mock_get_models:
            mock_models = [
                {
                    "elo_group": "mid",
                    "model_type": "xgb",
                    "version": "2025-10-18",
                    "accuracy": 0.75,
                    "training_date": "2025-10-18T13:17:40Z",
                    "feature_count": 150,
                    "training_samples": 1000,
                    "status": "active"
                },
                {
                    "elo_group": "low",
                    "model_type": "xgb",
                    "version": "2025-10-18",
                    "accuracy": 0.72,
                    "training_date": "2025-10-18T13:17:40Z",
                    "feature_count": 150,
                    "training_samples": 800,
                    "status": "active"
                }
            ]
            mock_get_models.return_value = mock_models
            
            response = client.get("/models/registry")
            
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert len(data["models"]) == 2
            assert data["models"][0]["elo_group"] == "mid"
            assert data["models"][1]["elo_group"] == "low"
    
    def test_get_models_registry_empty(self):
        """Test GET /models/registry with no models"""
        with patch('backend.services.model_registry.ModelRegistry.get_all_modelcards') as mock_get_models:
            mock_get_models.return_value = []
            
            response = client.get("/models/registry")
            
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert len(data["models"]) == 0
    
    def test_get_models_registry_error(self):
        """Test GET /models/registry with error"""
        with patch('backend.services.model_registry.ModelRegistry.get_all_modelcards') as mock_get_models:
            mock_get_models.side_effect = Exception("Registry error")
            
            response = client.get("/models/registry")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    def test_get_model_status(self):
        """Test GET /models/status returns model status"""
        with patch('backend.services.model_registry.ModelRegistry.get_model_status') as mock_get_status:
            mock_status = {
                "mid": {
                    "available": True,
                    "model_type": "xgb",
                    "version": "2025-10-18",
                    "last_loaded": "2025-10-18T13:17:40Z"
                },
                "low": {
                    "available": True,
                    "model_type": "xgb",
                    "version": "2025-10-18",
                    "last_loaded": "2025-10-18T13:17:40Z"
                },
                "high": {
                    "available": False,
                    "error": "Model not found"
                }
            }
            mock_get_status.return_value = mock_status
            
            response = client.get("/models/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "mid" in data
            assert "low" in data
            assert "high" in data
            assert data["mid"]["available"] is True
            assert data["high"]["available"] is False
    
    def test_get_model_status_error(self):
        """Test GET /models/status with error"""
        with patch('backend.services.model_registry.ModelRegistry.get_model_status') as mock_get_status:
            mock_get_status.side_effect = Exception("Status error")
            
            response = client.get("/models/status")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    def test_get_feature_map(self):
        """Test GET /models/feature-map returns feature map"""
        with patch('backend.services.inference.InferenceService.feature_map') as mock_feature_map:
            mock_feature_map.return_value = {
                "champ_index": {
                    "Annie": 0,
                    "Olaf": 1,
                    "Galio": 2
                },
                "id_to_index": {
                    "1": 0,
                    "2": 1,
                    "3": 2
                },
                "tags": {
                    "1": {"role": ["mage"], "damage": ["magic"]},
                    "2": {"role": ["fighter"], "damage": ["physical"]},
                    "3": {"role": ["tank"], "damage": ["magic"]}
                }
            }
            
            response = client.get("/models/feature-map")
            
            assert response.status_code == 200
            data = response.json()
            assert "champ_index" in data
            assert "id_to_index" in data
            assert "tags" in data
            assert "Annie" in data["champ_index"]
            assert data["champ_index"]["Annie"] == 0
    
    def test_get_feature_map_error(self):
        """Test GET /models/feature-map with error"""
        with patch('backend.services.inference.InferenceService.feature_map') as mock_feature_map:
            mock_feature_map.side_effect = Exception("Feature map error")
            
            response = client.get("/models/feature-map")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    def test_models_endpoints_require_auth(self):
        """Test that model endpoints require authentication"""
        # Test without API key
        response = client.get("/models/registry")
        assert response.status_code == 401
        
        response = client.get("/models/status")
        assert response.status_code == 401
        
        response = client.get("/models/feature-map")
        assert response.status_code == 401
    
    def test_models_endpoints_with_invalid_auth(self):
        """Test model endpoints with invalid API key"""
        response = client.get(
            "/models/registry",
            headers={"X-STRATMANCER-KEY": "invalid-key"}
        )
        assert response.status_code == 401
        
        response = client.get(
            "/models/status",
            headers={"X-STRATMANCER-KEY": "invalid-key"}
        )
        assert response.status_code == 401
        
        response = client.get(
            "/models/feature-map",
            headers={"X-STRATMANCER-KEY": "invalid-key"}
        )
        assert response.status_code == 401
    
    def test_models_endpoints_with_valid_auth(self):
        """Test model endpoints with valid API key"""
        with patch('backend.services.model_registry.ModelRegistry.get_all_modelcards') as mock_get_models:
            mock_get_models.return_value = []
            
            response = client.get(
                "/models/registry",
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            assert response.status_code == 200
        
        with patch('backend.services.model_registry.ModelRegistry.get_model_status') as mock_get_status:
            mock_get_status.return_value = {}
            
            response = client.get(
                "/models/status",
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            assert response.status_code == 200
        
        with patch('backend.services.inference.InferenceService.feature_map') as mock_feature_map:
            mock_feature_map.return_value = {}
            
            response = client.get(
                "/models/feature-map",
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            assert response.status_code == 200
    
    def test_model_registry_response_format(self):
        """Test model registry response format"""
        with patch('backend.services.model_registry.ModelRegistry.get_all_modelcards') as mock_get_models:
            mock_models = [
                {
                    "elo_group": "mid",
                    "model_type": "xgb",
                    "version": "2025-10-18",
                    "accuracy": 0.75,
                    "training_date": "2025-10-18T13:17:40Z",
                    "feature_count": 150,
                    "training_samples": 1000,
                    "status": "active"
                }
            ]
            mock_get_models.return_value = mock_models
            
            response = client.get(
                "/models/registry",
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "models" in data
            assert "total" in data
            assert "last_updated" in data
            
            # Check model structure
            model = data["models"][0]
            required_fields = [
                "elo_group", "model_type", "version", "accuracy",
                "training_date", "feature_count", "training_samples", "status"
            ]
            for field in required_fields:
                assert field in model
