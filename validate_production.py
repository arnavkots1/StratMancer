#!/usr/bin/env python3
"""
Production validation script for StratMancer
Tests all components of the production setup
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
API_BASE_URL = "http://localhost:8000"
WEB_BASE_URL = "http://localhost:3000"
TEST_API_KEY = "dev-key-change-in-production"

# Test data
VALID_PREDICT_REQUEST = {
    "elo": "mid",
    "patch": "15.20",
    "blue": {
        "top": 1,
        "jgl": 2,
        "mid": 3,
        "adc": 4,
        "sup": 5,
        "bans": [6, 7, 8, 9, 10]
    },
    "red": {
        "top": 11,
        "jgl": 12,
        "mid": 13,
        "adc": 14,
        "sup": 15,
        "bans": [16, 17, 18, 19, 20]
    }
}


class ProductionValidator:
    """Validates the complete production setup"""
    
    def __init__(self):
        self.results = {
            "docker": {"passed": 0, "failed": 0, "tests": []},
            "api": {"passed": 0, "failed": 0, "tests": []},
            "web": {"passed": 0, "failed": 0, "tests": []},
            "security": {"passed": 0, "failed": 0, "tests": []},
            "monitoring": {"passed": 0, "failed": 0, "tests": []},
            "performance": {"passed": 0, "failed": 0, "tests": []}
        }
    
    def log_test(self, category: str, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        result = "PASS" if passed else "FAIL"
        logger.info(f"[{category.upper()}] {test_name}: {result} {message}")
        
        self.results[category]["tests"].append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        
        if passed:
            self.results[category]["passed"] += 1
        else:
            self.results[category]["failed"] += 1
    
    def test_docker_services(self):
        """Test Docker services are running"""
        logger.info("Testing Docker services...")
        
        try:
            # Check if docker-compose is running
            result = subprocess.run(
                ["docker-compose", "ps", "--services", "--filter", "status=running"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                services = result.stdout.strip().split('\n')
                expected_services = ['api', 'web', 'redis']
                
                for service in expected_services:
                    if service in services:
                        self.log_test("docker", f"Service {service} running", True)
                    else:
                        self.log_test("docker", f"Service {service} running", False, "Service not found")
            else:
                self.log_test("docker", "Docker services check", False, result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_test("docker", "Docker services check", False, "Timeout")
        except FileNotFoundError:
            self.log_test("docker", "Docker services check", False, "docker-compose not found")
    
    def test_api_health(self):
        """Test API health endpoint"""
        logger.info("Testing API health...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/healthz", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("api", "Health endpoint", True)
                else:
                    self.log_test("api", "Health endpoint", False, f"Status: {data.get('status')}")
            else:
                self.log_test("api", "Health endpoint", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("api", "Health endpoint", False, str(e))
    
    def test_api_docs(self):
        """Test API documentation"""
        logger.info("Testing API documentation...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
            
            if response.status_code == 200:
                self.log_test("api", "API documentation", True)
            else:
                self.log_test("api", "API documentation", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("api", "API documentation", False, str(e))
    
    def test_api_prediction(self):
        """Test API prediction endpoint"""
        logger.info("Testing API prediction...")
        
        try:
            headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
            response = requests.post(
                f"{API_BASE_URL}/predict-draft",
                json=VALID_PREDICT_REQUEST,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "blue_win_prob" in data and "red_win_prob" in data:
                    self.log_test("api", "Prediction endpoint", True)
                else:
                    self.log_test("api", "Prediction endpoint", False, "Missing probability fields")
            else:
                self.log_test("api", "Prediction endpoint", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("api", "Prediction endpoint", False, str(e))
    
    def test_api_models(self):
        """Test API models endpoint"""
        logger.info("Testing API models...")
        
        try:
            headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
            response = requests.get(f"{API_BASE_URL}/models/registry", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "models" in data:
                    self.log_test("api", "Models registry", True)
                else:
                    self.log_test("api", "Models registry", False, "Missing models field")
            else:
                self.log_test("api", "Models registry", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("api", "Models registry", False, str(e))
    
    def test_web_interface(self):
        """Test web interface"""
        logger.info("Testing web interface...")
        
        try:
            response = requests.get(WEB_BASE_URL, timeout=5)
            
            if response.status_code == 200:
                self.log_test("web", "Web interface", True)
            else:
                self.log_test("web", "Web interface", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("web", "Web interface", False, str(e))
    
    def test_security_validation(self):
        """Test security features"""
        logger.info("Testing security features...")
        
        # Test oversized payload
        try:
            large_request = VALID_PREDICT_REQUEST.copy()
            large_request["blue"]["bans"] = list(range(1, 1000))  # Large payload
            
            headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
            response = requests.post(
                f"{API_BASE_URL}/predict-draft",
                json=large_request,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 413:
                self.log_test("security", "Payload size limit", True)
            else:
                self.log_test("security", "Payload size limit", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("security", "Payload size limit", False, str(e))
        
        # Test invalid champion ID
        try:
            invalid_request = VALID_PREDICT_REQUEST.copy()
            invalid_request["blue"]["top"] = 99999  # Invalid champion ID
            
            headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
            response = requests.post(
                f"{API_BASE_URL}/predict-draft",
                json=invalid_request,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 400:
                self.log_test("security", "Champion ID validation", True)
            else:
                self.log_test("security", "Champion ID validation", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("security", "Champion ID validation", False, str(e))
        
        # Test missing API key
        try:
            response = requests.post(
                f"{API_BASE_URL}/predict-draft",
                json=VALID_PREDICT_REQUEST,
                timeout=5
            )
            
            if response.status_code == 401:
                self.log_test("security", "API key validation", True)
            else:
                self.log_test("security", "API key validation", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("security", "API key validation", False, str(e))
    
    def test_monitoring_metrics(self):
        """Test monitoring and metrics"""
        logger.info("Testing monitoring...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            
            if response.status_code == 200:
                content = response.text
                if "stratmancer_requests_total" in content:
                    self.log_test("monitoring", "Prometheus metrics", True)
                else:
                    self.log_test("monitoring", "Prometheus metrics", False, "Missing metrics")
            else:
                self.log_test("monitoring", "Prometheus metrics", False, f"Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("monitoring", "Prometheus metrics", False, str(e))
    
    def test_performance(self):
        """Test performance requirements"""
        logger.info("Testing performance...")
        
        # Test response time
        try:
            start_time = time.time()
            headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
            response = requests.post(
                f"{API_BASE_URL}/predict-draft",
                json=VALID_PREDICT_REQUEST,
                headers=headers,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200 and duration < 1.0:
                self.log_test("performance", "Response time < 1s", True, f"{duration:.3f}s")
            else:
                self.log_test("performance", "Response time < 1s", False, f"{duration:.3f}s")
                
        except requests.exceptions.RequestException as e:
            self.log_test("performance", "Response time < 1s", False, str(e))
        
        # Test cold start (simulate by making multiple requests)
        try:
            times = []
            for i in range(3):
                start_time = time.time()
                headers = {"X-STRATMANCER-KEY": TEST_API_KEY}
                response = requests.post(
                    f"{API_BASE_URL}/predict-draft",
                    json=VALID_PREDICT_REQUEST,
                    headers=headers,
                    timeout=10
                )
                duration = time.time() - start_time
                times.append(duration)
                time.sleep(0.1)  # Small delay between requests
            
            avg_time = sum(times) / len(times)
            if avg_time < 0.5:  # Average should be under 500ms
                self.log_test("performance", "Average response time", True, f"{avg_time:.3f}s")
            else:
                self.log_test("performance", "Average response time", False, f"{avg_time:.3f}s")
                
        except requests.exceptions.RequestException as e:
            self.log_test("performance", "Average response time", False, str(e))
    
    def run_all_tests(self):
        """Run all validation tests"""
        logger.info("Starting production validation...")
        
        self.test_docker_services()
        self.test_api_health()
        self.test_api_docs()
        self.test_api_prediction()
        self.test_api_models()
        self.test_web_interface()
        self.test_security_validation()
        self.test_monitoring_metrics()
        self.test_performance()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 70)
        logger.info("PRODUCTION VALIDATION SUMMARY")
        logger.info("=" * 70)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.results.items():
            passed = results["passed"]
            failed = results["failed"]
            total = passed + failed
            
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            logger.info(f"{category.upper():12} {status} ({passed}/{total} tests passed)")
            
            # Show failed tests
            for test in results["tests"]:
                if not test["passed"]:
                    logger.info(f"  ❌ {test['name']}: {test['message']}")
        
        logger.info("=" * 70)
        overall_status = "✅ PASS" if total_failed == 0 else "❌ FAIL"
        logger.info(f"OVERALL: {overall_status} ({total_passed}/{total_passed + total_failed} tests passed)")
        logger.info("=" * 70)
        
        if total_failed == 0:
            logger.info("🎉 All tests passed! StratMancer is production-ready!")
        else:
            logger.info(f"⚠️  {total_failed} tests failed. Please review and fix issues.")
        
        return total_failed == 0


def main():
    """Main validation function"""
    validator = ProductionValidator()
    success = validator.run_all_tests()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
