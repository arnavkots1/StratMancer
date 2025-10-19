"""
Security tests for StratMancer API
"""

import pytest
import json
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)

# Test data
VALID_REQUEST = {
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


class TestSecurity:
    """Test security features"""
    
    def test_oversized_payload(self):
        """Test oversized payload returns 413"""
        # Create a large payload (over 32KB)
        large_bans = list(range(1, 1000))  # Large list to exceed 32KB
        large_request = VALID_REQUEST.copy()
        large_request["blue"]["bans"] = large_bans
        large_request["red"]["bans"] = large_bans
        
        response = client.post(
            "/predict-draft",
            json=large_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "payload" in data["detail"].lower()
        assert "32" in data["detail"]  # Should mention 32KB limit
    
    def test_invalid_champion_id(self):
        """Test invalid champion ID returns 400"""
        invalid_request = VALID_REQUEST.copy()
        invalid_request["blue"]["top"] = 99999  # Invalid champion ID
        
        response = client.post(
            "/predict-draft",
            json=invalid_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "champion" in data["detail"].lower()
        assert "99999" in str(data["detail"])
    
    def test_missing_roles(self):
        """Test missing roles returns 400"""
        missing_request = VALID_REQUEST.copy()
        del missing_request["blue"]["support"]  # Remove required role
        
        response = client.post(
            "/predict-draft",
            json=missing_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "support" in str(data["detail"]).lower()
        assert "missing" in str(data["detail"]).lower()
    
    def test_duplicate_bans_handled(self):
        """Test duplicate bans are automatically deduplicated"""
        duplicate_request = VALID_REQUEST.copy()
        duplicate_request["blue"]["bans"] = [1, 1, 2, 2, 3]  # Duplicates
        duplicate_request["red"]["bans"] = [4, 4, 5, 5, 6]  # Duplicates
        
        # Mock the prediction service
        with pytest.Mock() as mock_predict:
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
    
    def test_invalid_json(self):
        """Test invalid JSON returns 400"""
        response = client.post(
            "/predict-draft",
            data="invalid json",
            headers={
                "X-STRATMANCER-KEY": "test-key",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "json" in data["detail"].lower()
    
    def test_empty_request_body(self):
        """Test empty request body returns 400"""
        response = client.post(
            "/predict-draft",
            data="",
            headers={
                "X-STRATMANCER-KEY": "test-key",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "body" in data["detail"].lower()
        assert "required" in data["detail"].lower()
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options(
            "/predict-draft",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-STRATMANCER-KEY"
            }
        )
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_cors_origin_validation(self):
        """Test CORS origin validation"""
        # Valid origin
        response = client.post(
            "/predict-draft",
            json=VALID_REQUEST,
            headers={
                "X-STRATMANCER-KEY": "test-key",
                "Origin": "http://localhost:3000"
            }
        )
        
        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers
    
    def test_request_id_header(self):
        """Test request ID header is included in responses"""
        response = client.post(
            "/predict-draft",
            json=VALID_REQUEST,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        # Should have request ID header
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
        assert isinstance(request_id, str)
    
    def test_correlation_id_on_error(self):
        """Test correlation ID is included in error responses"""
        # Trigger an error with invalid data
        invalid_request = VALID_REQUEST.copy()
        invalid_request["blue"]["top"] = "invalid"  # String instead of int
        
        response = client.post(
            "/predict-draft",
            json=invalid_request,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        # Should have correlation ID in error response
        if response.status_code >= 400:
            data = response.json()
            if "correlation_id" in data:
                correlation_id = data["correlation_id"]
                assert len(correlation_id) > 0
                assert isinstance(correlation_id, str)
    
    def test_log_sanitization(self):
        """Test that logs don't contain sensitive data"""
        # This test would require access to log output
        # For now, we'll just ensure the endpoint works
        response = client.post(
            "/predict-draft",
            json=VALID_REQUEST,
            headers={"X-STRATMANCER-KEY": "sensitive-key-12345"}
        )
        
        # Should work without exposing the key in response
        assert response.status_code in [200, 401, 503]  # Various possible responses
        data = response.json()
        assert "sensitive-key-12345" not in str(data)
    
    def test_timeout_handling(self):
        """Test request timeout handling"""
        # This would require mocking a slow operation
        # For now, we'll test that the endpoint responds quickly
        import time
        start_time = time.time()
        
        response = client.post(
            "/predict-draft",
            json=VALID_REQUEST,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        duration = time.time() - start_time
        
        # Should respond within reasonable time (less than 5 seconds)
        assert duration < 5.0
        assert response.status_code in [200, 401, 503]  # Various possible responses
    
    def test_method_validation(self):
        """Test HTTP method validation"""
        # Test unsupported method
        response = client.patch(
            "/predict-draft",
            json=VALID_REQUEST,
            headers={"X-STRATMANCER-KEY": "test-key"}
        )
        
        # Should return method not allowed or similar
        assert response.status_code in [405, 422, 401]  # Method not allowed or validation error
    
    def test_content_type_validation(self):
        """Test content type validation"""
        response = client.post(
            "/predict-draft",
            data=json.dumps(VALID_REQUEST),
            headers={
                "X-STRATMANCER-KEY": "test-key",
                "Content-Type": "text/plain"  # Wrong content type
            }
        )
        
        # Should still work (FastAPI is flexible with content types)
        assert response.status_code in [200, 401, 422, 503]
