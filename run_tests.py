#!/usr/bin/env python3
"""
Comprehensive Test Runner for Code Grader API
=============================================

This script runs all unit tests for the Code Grader API project with:
- Proper Django configuration
- Test discovery and execution
- Coverage reporting
- Performance metrics
- Test result summary

Usage:
    python run_tests.py [options]

Options:
    --coverage          Run with coverage reporting
    --verbose          Verbose output
    --parallel         Run tests in parallel
    --apps             Run tests for specific apps (comma-separated)
    --pattern          Test pattern to match
    --failfast         Stop on first failure
    --keepdb           Keep test database between runs
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_grader_api.settings')

import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line


def setup_test_environment():
    """Setup test environment"""
    print("🔧 Setting up test environment...")
    
    # Configure Django
    django.setup()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Set test-specific settings
    settings.DEBUG = False
    settings.CACHE_TIMEOUT = 60  # Shorter cache timeout for tests
    
    print("✅ Test environment ready")


def run_migrations():
    """Run database migrations for testing"""
    print("🗄️  Running database migrations...")
    
    try:
        # Run migrations
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Migrations completed")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True


def run_tests_with_coverage():
    """Run tests with coverage reporting"""
    print("📊 Running tests with coverage...")
    
    try:
        # Install coverage if not available
        try:
            import coverage
        except ImportError:
            print("📦 Installing coverage...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'coverage'])
            import coverage
        
        # Run coverage
        cov = coverage.Coverage(
            source=['evaluation', 'analytics_service', 'metrics_service'],
            omit=[
                '*/tests.py',
                '*/migrations/*',
                '*/__pycache__/*',
                '*/venv/*',
                '*/env/*'
            ]
        )
        cov.start()
        
        # Run tests
        test_runner = get_runner(settings)
        runner = test_runner(verbosity=2, interactive=False)
        failures = runner.run_tests([
            'evaluation.tests',
            'analytics_service.tests',
            'metrics_service.tests'
        ])
        
        cov.stop()
        cov.save()
        
        # Generate coverage report
        print("\n📈 Coverage Report:")
        cov.report()
        
        # Generate HTML report
        cov.html_report(directory='htmlcov')
        print("📁 HTML coverage report generated in 'htmlcov/' directory")
        
        return failures == 0
        
    except Exception as e:
        print(f"❌ Coverage test failed: {e}")
        return False


def run_tests_parallel():
    """Run tests in parallel"""
    print("⚡ Running tests in parallel...")
    
    try:
        # Install pytest-xdist if not available
        try:
            import pytest
        except ImportError:
            print("📦 Installing pytest and pytest-xdist...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest', 'pytest-django', 'pytest-xdist'])
        
        # Run tests with pytest
        cmd = [
            sys.executable, '-m', 'pytest',
            '--ds=code_grader_api.settings',
            '--tb=short',
            '-n', 'auto',  # Auto-detect number of workers
            'evaluation/tests.py',
            'analytics_service/tests.py',
            'metrics_service/tests.py'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Parallel test failed: {e}")
        return False


def run_standard_tests(verbose=False, apps=None, pattern=None, failfast=False, keepdb=False):
    """Run standard Django tests"""
    print("🧪 Running standard Django tests...")
    
    start_time = time.time()
    
    try:
        # Build test command
        cmd = ['manage.py', 'test']
        
        if verbose:
            cmd.append('--verbosity=2')
        else:
            cmd.append('--verbosity=1')
        
        if failfast:
            cmd.append('--failfast')
        
        if keepdb:
            cmd.append('--keepdb')
        
        if apps:
            cmd.extend(apps.split(','))
        else:
            cmd.extend([
                'evaluation.tests',
                'analytics_service.tests',
                'metrics_service.tests'
            ])
        
        if pattern:
            cmd.extend(['--pattern', pattern])
        
        # Run tests
        execute_from_command_line(cmd)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Tests completed in {duration:.2f} seconds")
        return True
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


def run_specific_test_suites():
    """Run specific test suites"""
    print("🎯 Running specific test suites...")
    
    test_suites = [
        ('Evaluation Tests', 'evaluation.tests'),
        ('Analytics Tests', 'analytics_service.tests'),
        ('Metrics Tests', 'metrics_service.tests')
    ]
    
    results = {}
    
    for suite_name, suite_path in test_suites:
        print(f"\n🔍 Running {suite_name}...")
        start_time = time.time()
        
        try:
            cmd = ['manage.py', 'test', suite_path, '--verbosity=2']
            execute_from_command_line(cmd)
            
            end_time = time.time()
            duration = end_time - start_time
            results[suite_name] = {'status': 'PASS', 'duration': duration}
            print(f"✅ {suite_name} completed in {duration:.2f} seconds")
            
        except Exception as e:
            results[suite_name] = {'status': 'FAIL', 'error': str(e)}
            print(f"❌ {suite_name} failed: {e}")
    
    return results


def run_performance_tests():
    """Run performance tests"""
    print("⚡ Running performance tests...")
    
    try:
        # Test rate limiting
        print("  🔒 Testing rate limiting...")
        cmd = ['manage.py', 'test', 'evaluation.tests.RateLimitTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        # Test caching
        print("  💾 Testing caching...")
        cmd = ['manage.py', 'test', 'evaluation.tests.CacheTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        # Test analytics caching
        print("  📊 Testing analytics caching...")
        cmd = ['manage.py', 'test', 'analytics_service.tests.AnalyticsCacheTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        # Test metrics caching
        print("  📈 Testing metrics caching...")
        cmd = ['manage.py', 'test', 'metrics_service.tests.MetricsCacheTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        print("✅ Performance tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running integration tests...")
    
    try:
        # Test complete evaluation flow
        print("  🔄 Testing complete evaluation flow...")
        cmd = ['manage.py', 'test', 'evaluation.tests.IntegrationTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        # Test complete analytics flow
        print("  📊 Testing complete analytics flow...")
        cmd = ['manage.py', 'test', 'analytics_service.tests.AnalyticsIntegrationTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        # Test complete metrics flow
        print("  📈 Testing complete metrics flow...")
        cmd = ['manage.py', 'test', 'metrics_service.tests.MetricsIntegrationTest', '--verbosity=1']
        execute_from_command_line(cmd)
        
        print("✅ Integration tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False


def generate_test_report(results):
    """Generate test report"""
    print("\n" + "="*60)
    print("📋 TEST REPORT")
    print("="*60)
    
    total_suites = len(results)
    passed_suites = sum(1 for r in results.values() if r['status'] == 'PASS')
    failed_suites = total_suites - passed_suites
    
    print(f"Total Test Suites: {total_suites}")
    print(f"Passed: {passed_suites}")
    print(f"Failed: {failed_suites}")
    print(f"Success Rate: {(passed_suites/total_suites)*100:.1f}%")
    
    print("\nDetailed Results:")
    for suite_name, result in results.items():
        status_icon = "✅" if result['status'] == 'PASS' else "❌"
        duration = f" ({result['duration']:.2f}s)" if 'duration' in result else ""
        error = f" - {result['error']}" if 'error' in result else ""
        print(f"  {status_icon} {suite_name}{duration}{error}")
    
    print("="*60)


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Code Grader API Test Runner')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--apps', type=str, help='Run tests for specific apps (comma-separated)')
    parser.add_argument('--pattern', type=str, help='Test pattern to match')
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')
    parser.add_argument('--keepdb', action='store_true', help='Keep test database between runs')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--suites', action='store_true', help='Run specific test suites')
    
    args = parser.parse_args()
    
    print("🚀 Code Grader API Test Runner")
    print("="*50)
    
    # Setup environment
    setup_test_environment()
    
    # Run migrations
    if not run_migrations():
        print("❌ Failed to setup test database")
        sys.exit(1)
    
    success = True
    
    try:
        if args.performance:
            # Run performance tests only
            success = run_performance_tests()
        elif args.integration:
            # Run integration tests only
            success = run_integration_tests()
        elif args.suites:
            # Run specific test suites
            results = run_specific_test_suites()
            generate_test_report(results)
            success = all(r['status'] == 'PASS' for r in results.values())
        elif args.coverage:
            # Run tests with coverage
            success = run_tests_with_coverage()
        elif args.parallel:
            # Run tests in parallel
            success = run_tests_parallel()
        else:
            # Run standard tests
            success = run_standard_tests(
                verbose=args.verbose,
                apps=args.apps,
                pattern=args.pattern,
                failfast=args.failfast,
                keepdb=args.keepdb
            )
        
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 