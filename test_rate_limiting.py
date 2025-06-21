#!/usr/bin/env python3
"""
Rate Limiting Test Script
=========================

This script tests the rate limiting functionality by making rapid requests
to various API endpoints to verify that rate limiting is working correctly.

Usage:
    python test_rate_limiting.py [endpoint] [requests]

Examples:
    python test_rate_limiting.py health 150
    python test_rate_limiting.py evaluate 15
    python test_rate_limiting.py analytics 70
"""

import requests
import time
import sys
import json
from datetime import datetime


class RateLimitTester:
    """Test rate limiting functionality"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'rate_limited_requests': 0,
            'other_errors': 0,
            'start_time': None,
            'end_time': None,
            'responses': []
        }
    
    def test_endpoint(self, endpoint, num_requests, delay=0.01):
        """Test rate limiting for a specific endpoint"""
        print(f"🔒 Testing rate limiting for endpoint: {endpoint}")
        print(f"📊 Making {num_requests} requests with {delay}s delay between requests")
        print("-" * 60)
        
        self.results['start_time'] = datetime.now()
        
        endpoint_urls = {
            'health': f"{self.base_url}/api/evaluation/health/",
            'evaluate': f"{self.base_url}/api/evaluation/evaluate/",
            'analytics': f"{self.base_url}/api/analytics/labs/",
            'metrics': f"{self.base_url}/api/metrics/summary/",
            'rubrics': f"{self.base_url}/api/evaluation/rubrics/",
            'stats': f"{self.base_url}/api/evaluation/stats/"
        }
        
        if endpoint not in endpoint_urls:
            print(f"❌ Unknown endpoint: {endpoint}")
            print(f"Available endpoints: {', '.join(endpoint_urls.keys())}")
            return
        
        url = endpoint_urls[endpoint]
        
        # Prepare test data for POST requests
        test_data = None
        if endpoint == 'evaluate':
            test_data = {
                "student_id": "TEST123",
                "name": "Test Student",
                "section": "14",
                "term": "Spring 2025",
                "instructor_name": "Dr. Test",
                "lab_name": "Test Lab",
                "input": "Download test.py\nprint('Hello World')"
            }
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                
                if test_data:
                    response = self.session.post(url, json=test_data, timeout=5)
                else:
                    response = self.session.get(url, timeout=5)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                self.results['total_requests'] += 1
                
                if response.status_code == 200:
                    self.results['successful_requests'] += 1
                    status = "✅ SUCCESS"
                elif response.status_code == 429:
                    self.results['rate_limited_requests'] += 1
                    status = "🚫 RATE LIMITED"
                else:
                    self.results['other_errors'] += 1
                    status = f"❌ ERROR {response.status_code}"
                
                # Store response details
                self.results['responses'].append({
                    'request_number': i + 1,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"Request {i+1:3d}: {status} - {response.status_code} ({response_time:.1f}ms)")
                
                # Add delay between requests
                if delay > 0:
                    time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                self.results['total_requests'] += 1
                self.results['other_errors'] += 1
                print(f"Request {i+1:3d}: ❌ REQUEST ERROR - {str(e)}")
                
                self.results['responses'].append({
                    'request_number': i + 1,
                    'status_code': None,
                    'response_time_ms': None,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.results['end_time'] = datetime.now()
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📋 RATE LIMITING TEST SUMMARY")
        print("="*60)
        
        total_time = (self.results['end_time'] - self.results['start_time']).total_seconds()
        
        print(f"Total Requests: {self.results['total_requests']}")
        print(f"Successful: {self.results['successful_requests']}")
        print(f"Rate Limited: {self.results['rate_limited_requests']}")
        print(f"Other Errors: {self.results['other_errors']}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Requests per Second: {self.results['total_requests']/total_time:.2f}")
        
        if self.results['rate_limited_requests'] > 0:
            print(f"Rate Limiting Success Rate: {(self.results['rate_limited_requests']/self.results['total_requests'])*100:.1f}%")
            print("✅ Rate limiting is working correctly!")
        else:
            print("⚠️  No rate limiting detected - may need more requests or faster rate")
        
        # Calculate average response times
        successful_responses = [r for r in self.results['responses'] if r['status_code'] == 200]
        if successful_responses:
            avg_response_time = sum(r['response_time_ms'] for r in successful_responses) / len(successful_responses)
            print(f"Average Response Time: {avg_response_time:.1f}ms")
        
        print("="*60)
    
    def save_results(self, filename=None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rate_limit_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"📁 Results saved to: {filename}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_rate_limiting.py [endpoint] [requests]")
        print("\nEndpoints:")
        print("  health     - Health check (120/min limit)")
        print("  evaluate   - Evaluation endpoint (10/min limit)")
        print("  analytics  - Analytics endpoint (60/min limit)")
        print("  metrics    - Metrics endpoint (60/min limit)")
        print("  rubrics    - Rubrics endpoint (60/min limit)")
        print("  stats      - Stats endpoint (60/min limit)")
        print("\nExamples:")
        print("  python test_rate_limiting.py health 150")
        print("  python test_rate_limiting.py evaluate 15")
        print("  python test_rate_limiting.py analytics 70")
        return
    
    endpoint = sys.argv[1]
    num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    # Adjust delay based on endpoint
    delays = {
        'health': 0.01,      # Fast for health check
        'evaluate': 0.1,     # Slower for evaluation
        'analytics': 0.05,   # Medium for analytics
        'metrics': 0.05,     # Medium for metrics
        'rubrics': 0.05,     # Medium for rubrics
        'stats': 0.05        # Medium for stats
    }
    
    delay = delays.get(endpoint, 0.05)
    
    tester = RateLimitTester()
    tester.test_endpoint(endpoint, num_requests, delay)
    tester.save_results()


if __name__ == '__main__':
    main() 