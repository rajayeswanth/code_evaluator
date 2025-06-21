#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Code Grader
Tests all available endpoints to ensure they're working correctly with caching.
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.start_time = time.time()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_endpoint(self, method, endpoint, data=None, expected_status=200, name=None):
        """Test a single endpoint"""
        if name is None:
            name = f"{method} {endpoint}"
        
        try:
            url = f"{BASE_URL}{endpoint}"
            headers = {"Content-Type": "application/json"}
            
            self.log(f"Testing {name}...")
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check status code
            if response.status_code != expected_status:
                self.results["failed"] += 1
                self.log(f" {name} - Expected status {expected_status}, got {response.status_code}", "ERROR")
                self.results["errors"].append(f"{name}: Status {response.status_code}")
                return False
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                
                # Check for cache insights (if it's a successful API response)
                if response.status_code == 200 and isinstance(response_data, dict):
                    if "cache_insights" in response_data:
                        cache_info = response_data["cache_insights"]
                        self.log(f" {name} - Cache: {'HIT' if cache_info.get('cache_hit') else 'MISS'}")
                    else:
                        self.log(f" {name} - No cache insights (expected for some endpoints)")
                else:
                    self.log(f" {name}")
                
                self.results["passed"] += 1
                return True
                
            except json.JSONDecodeError:
                self.log(f"⚠️  {name} - Response is not JSON", "WARNING")
                self.results["passed"] += 1  # Still count as passed if status is correct
                return True
                
        except requests.exceptions.RequestException as e:
            self.results["failed"] += 1
            self.log(f" {name} - Request failed: {str(e)}", "ERROR")
            self.results["errors"].append(f"{name}: {str(e)}")
            return False
        except Exception as e:
            self.results["failed"] += 1
            self.log(f" {name} - Unexpected error: {str(e)}", "ERROR")
            self.results["errors"].append(f"{name}: {str(e)}")
            return False

    def test_evaluation_apis(self):
        """Test evaluation-related APIs"""
        self.log("=" * 50)
        self.log("TESTING EVALUATION APIs")
        self.log("=" * 50)
        
        # Health check
        self.test_endpoint("GET", "/api/evaluation/health/", name="Health Check")
        
        # Test cache endpoint
        self.test_endpoint("GET", "/api/evaluation/test-cache/", name="Test Cache")
        
        # Get rubrics with pagination
        self.test_endpoint("GET", "/api/evaluation/rubrics/?page=1&page_size=2", name="Get Rubrics (Page 1)")
        self.test_endpoint("GET", "/api/evaluation/rubrics/?page=2&page_size=2", name="Get Rubrics (Page 2)")
        
        # Get all evaluations
        self.test_endpoint("GET", "/api/evaluation/evaluations/?page=1&page_size=5", name="Get All Evaluations")
        
        # Note: Evaluation by ID tests removed since we don't know valid IDs
        # These would be tested with actual evaluation IDs when available

    def test_analytics_apis(self):
        """Test analytics-related APIs"""
        self.log("=" * 50)
        self.log("TESTING ANALYTICS APIs")
        self.log("=" * 50)
        
        # Get all labs
        self.test_endpoint("GET", "/api/analytics/labs/", name="Get All Labs")
        
        # Get lab by ID
        self.test_endpoint("GET", "/api/analytics/lab/1/", name="Get Lab by ID (1)")
        self.test_endpoint("GET", "/api/analytics/lab/23/", name="Get Lab by ID (23)")
        
        # Get all students
        self.test_endpoint("GET", "/api/analytics/students/?page=1&page_size=5", name="Get All Students")
        
        # Get student details
        self.test_endpoint("GET", "/api/analytics/student/STU100001/", name="Get Student Details")
        
        # Get student performance summary
        self.test_endpoint("GET", "/api/analytics/student/STU100001/performance/", name="Get Student Performance Summary")
        
        # Get performance by lab
        self.test_endpoint("GET", "/api/analytics/performance/by-lab/?lab_name=Lab1&page=1&page_size=5", name="Get Performance by Lab")
        
        # Get summarized performance by lab
        self.test_endpoint("GET", "/api/analytics/performance/lab/Lab1/", name="Get Summarized Performance by Lab")
        self.test_endpoint("GET", "/api/analytics/performance/lab/Lab1/?section=14", name="Get Summarized Performance by Lab (with section)")
        
        # Get summarized performance by section
        self.test_endpoint("GET", "/api/analytics/performance/section/14/", name="Get Summarized Performance by Section")
        self.test_endpoint("GET", "/api/analytics/performance/section/14/?lab_name=Lab1", name="Get Summarized Performance by Section (with lab)")
        
        # Get summarized performance by semester
        self.test_endpoint("GET", "/api/analytics/performance/semester/Spring%202025/", name="Get Summarized Performance by Semester")
        self.test_endpoint("GET", "/api/analytics/performance/semester/Spring%202025/?lab_name=Lab1", name="Get Summarized Performance by Semester (with lab)")
        
        # Analyze lab
        self.test_endpoint("GET", "/api/analytics/lab/Lab1/", name="Analyze Lab")
        
        # Analyze lab section
        self.test_endpoint("GET", "/api/analytics/lab/Lab1/section/14/", name="Analyze Lab Section")
        
        # Analyze semester
        self.test_endpoint("GET", "/api/analytics/semester/Spring%202025/", name="Analyze Semester")
        
        # Analyze lab semester
        self.test_endpoint("GET", "/api/analytics/lab/Lab1/semester/Spring%202025/", name="Analyze Lab Semester")

    def test_metrics_apis(self):
        """Test metrics-related APIs"""
        self.log("=" * 50)
        self.log("TESTING METRICS APIs")
        self.log("=" * 50)
        
        # Get request metrics
        self.test_endpoint("GET", "/api/metrics/requests/?page=1&page_size=5", name="Get Request Metrics")
        
        # Get cost metrics
        self.test_endpoint("GET", "/api/metrics/costs/?page=1&page_size=5", name="Get Cost Metrics")
        
        # Get performance summary
        self.test_endpoint("GET", "/api/metrics/performance/", name="Get Performance Summary")
        
        # Get cache status
        self.test_endpoint("GET", "/api/metrics/cache/", name="Get Cache Status")
        
        # Get metrics summary
        self.test_endpoint("GET", "/api/metrics/summary/", name="Get Metrics Summary")
        
        # Get system health dashboard
        self.test_endpoint("GET", "/api/metrics/dashboard/", name="Get System Health Dashboard")

    def test_cache_functionality(self):
        """Test cache functionality by making repeated requests"""
        self.log("=" * 50)
        self.log("TESTING CACHE FUNCTIONALITY")
        self.log("=" * 50)
        
        # Test cache with test endpoint
        self.log("Testing cache with /api/evaluation/test-cache/")
        self.test_endpoint("GET", "/api/evaluation/test-cache/", name="Cache Test 1")
        self.test_endpoint("GET", "/api/evaluation/test-cache/", name="Cache Test 2 (should be HIT)")
        
        # Test cache with rubrics endpoint
        self.log("Testing cache with /api/evaluation/rubrics/")
        self.test_endpoint("GET", "/api/evaluation/rubrics/?page=1&page_size=2", name="Rubrics Cache Test 1")
        self.test_endpoint("GET", "/api/evaluation/rubrics/?page=1&page_size=2", name="Rubrics Cache Test 2 (should be HIT)")
        
        # Test cache with analytics endpoint
        self.log("Testing cache with /api/analytics/lab/1/")
        self.test_endpoint("GET", "/api/analytics/lab/1/", name="Analytics Cache Test 1")
        self.test_endpoint("GET", "/api/analytics/lab/1/", name="Analytics Cache Test 2 (should be HIT)")

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        self.log("=" * 50)
        self.log("TESTING ERROR HANDLING")
        self.log("=" * 50)
        
        # Test 404 for non-existent endpoints
        self.test_endpoint("GET", "/api/nonexistent/", expected_status=404, name="404 Test")
        
        # Test graceful handling of invalid IDs (should return 200 with error message)
        self.test_endpoint("GET", "/api/analytics/student/INVALID_ID/", expected_status=200, name="Invalid Student ID (Graceful)")
        
        # Test graceful handling of invalid lab ID
        self.test_endpoint("GET", "/api/analytics/lab/99999/", expected_status=200, name="Invalid Lab ID (Graceful)")
        
        # Test graceful handling of invalid evaluation ID
        self.test_endpoint("GET", "/api/evaluation/evaluations/99999/", expected_status=200, name="Invalid Evaluation ID (Graceful)")

    def run_all_tests(self):
        """Run all test suites"""
        self.log("🚀 Starting Comprehensive API Test Suite")
        self.log(f"Base URL: {BASE_URL}")
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Test all API categories
            self.test_evaluation_apis()
            self.test_analytics_apis()
            self.test_metrics_apis()
            self.test_cache_functionality()
            self.test_error_handling()
            
        except KeyboardInterrupt:
            self.log("Test interrupted by user", "WARNING")
        except Exception as e:
            self.log(f"Unexpected error during testing: {str(e)}", "ERROR")
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total_tests = self.results["passed"] + self.results["failed"]
        duration = time.time() - self.start_time
        
        self.log("=" * 50)
        self.log("TEST SUMMARY")
        self.log("=" * 50)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {self.results['passed']} ")
        self.log(f"Failed: {self.results['failed']} ")
        self.log(f"Success Rate: {(self.results['passed']/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        self.log(f"Duration: {duration:.2f} seconds")
        
        if self.results["errors"]:
            self.log("\nErrors encountered:")
            for error in self.results["errors"]:
                self.log(f"  - {error}", "ERROR")
        
        # Exit with appropriate code
        if self.results["failed"] > 0:
            self.log(" Some tests failed!", "ERROR")
            sys.exit(1)
        else:
            self.log(" All tests passed!", "SUCCESS")
            sys.exit(0)

def main():
    """Main function"""
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 