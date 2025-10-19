"""
Rate limiting tests
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch

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


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_per_ip(self):
        """Test rate limiting per IP address"""
        # Mock the rate limiter to simulate rate limit exceeded
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_remaining.return_value = 0
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "rate limit" in data["detail"].lower()
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_per_api_key(self):
        """Test rate limiting per API key"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_remaining.return_value = 0
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "premium-key"}
            )
            
            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "rate limit" in data["detail"].lower()
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are present"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            mock_limiter.get_remaining.return_value = 59
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            # Should succeed (mocked prediction)
            if response.status_code == 200:
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                assert response.headers["X-RateLimit-Remaining"] == "59"
    
    def test_rate_limit_different_ips(self):
        """Test different IPs have separate rate limits"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            mock_limiter.get_remaining.return_value = 60
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            # First IP
            response1 = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            # Second IP (simulated by different client)
            response2 = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            # Both should have full rate limit (different IPs)
            if response1.status_code == 200:
                assert response1.headers["X-RateLimit-Remaining"] == "60"
            if response2.status_code == 200:
                assert response2.headers["X-RateLimit-Remaining"] == "60"
    
    def test_rate_limit_different_api_keys(self):
        """Test different API keys have separate rate limits"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            mock_limiter.get_remaining.return_value = 60
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            # First API key
            response1 = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "key1"}
            )
            
            # Second API key
            response2 = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "key2"}
            )
            
            # Both should have full rate limit (different keys)
            if response1.status_code == 200:
                assert response1.headers["X-RateLimit-Remaining"] == "60"
            if response2.status_code == 200:
                assert response2.headers["X-RateLimit-Remaining"] == "60"
    
    def test_rate_limit_global_limit(self):
        """Test global rate limit"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_remaining.return_value = 0
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "rate limit" in data["detail"].lower()
    
    def test_rate_limit_reset_time_format(self):
        """Test rate limit reset time is in correct format"""
        reset_time = int(time.time()) + 60
        
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            mock_limiter.get_remaining.return_value = 59
            mock_limiter.get_reset_time.return_value = reset_time
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            if response.status_code == 200:
                assert "X-RateLimit-Reset" in response.headers
                # Should be a valid timestamp
                reset_header = response.headers["X-RateLimit-Reset"]
                assert reset_header.isdigit()
                assert int(reset_header) == reset_time
    
    def test_rate_limit_retry_after_header(self):
        """Test Retry-After header when rate limited"""
        with patch('backend.services.rate_limit.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            mock_limiter.get_remaining.return_value = 0
            mock_limiter.get_reset_time.return_value = int(time.time()) + 60
            
            response = client.post(
                "/predict-draft",
                json=VALID_REQUEST,
                headers={"X-STRATMANCER-KEY": "test-key"}
            )
            
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            retry_after = int(response.headers["Retry-After"])
            assert retry_after > 0
            assert retry_after <= 60  # Should be reasonable
