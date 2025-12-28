#!/usr/bin/env python
"""
Comprehensive test script for health check endpoints.

This script tests all health check endpoints:
- /health/ - Overall health check
- /health/db/ - Database health check
- /health/redis/ - Redis health check

Usage:
    python test_health_checks.py
    # Or in Docker:
    docker-compose exec web python test_health_checks.py
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from django.conf import settings

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_header(message):
    """Print header message."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def test_overall_health_check(base_url='http://localhost:8000'):
    """Test overall health check endpoint."""
    print_header("Testing Overall Health Check (/health/)")
    
    try:
        url = f"{base_url}/health/"
        print_info(f"Testing: {url}")
        
        response = requests.get(url, timeout=5)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Health check endpoint is accessible")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Version: {data.get('version', 'unknown')}")
            print_info(f"Timestamp: {data.get('timestamp', 'unknown')}")
            print_info(f"Response Time: {data.get('response_time_ms', 0):.2f}ms")
            
            if 'services' in data:
                print_info("\nService Status:")
                for service, status_info in data['services'].items():
                    if isinstance(status_info, dict):
                        status = status_info.get('status', 'unknown')
                        response_time = status_info.get('response_time_ms', 0)
                        print_info(f"  - {service}: {status} ({response_time:.2f}ms)")
                    else:
                        print_info(f"  - {service}: {status_info}")
            
            if data.get('status') == 'healthy':
                print_success("All services are healthy!")
                return True
            else:
                print_warning("Some services are unhealthy")
                return False
        else:
            print_error(f"Health check failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Is the server running?")
        print_info("Try: docker-compose up -d")
        return False
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_database_health_check(base_url='http://localhost:8000'):
    """Test database health check endpoint."""
    print_header("Testing Database Health Check (/health/db/)")
    
    try:
        url = f"{base_url}/health/db/"
        print_info(f"Testing: {url}")
        
        response = requests.get(url, timeout=5)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Database health check endpoint is accessible")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Timestamp: {data.get('timestamp', 'unknown')}")
            
            if 'database' in data:
                db_info = data['database']
                print_info("\nDatabase Information:")
                print_info(f"  - Engine: {db_info.get('engine', 'unknown')}")
                print_info(f"  - Name: {db_info.get('name', 'unknown')}")
                print_info(f"  - Host: {db_info.get('host', 'unknown')}")
                print_info(f"  - Port: {db_info.get('port', 'unknown')}")
                print_info(f"  - Response Time: {db_info.get('response_time_ms', 0):.2f}ms")
                
                if 'connection_id' in db_info:
                    print_info(f"  - Connection ID: {db_info.get('connection_id')}")
                if 'actual_database' in db_info:
                    print_info(f"  - Actual Database: {db_info.get('actual_database')}")
            
            if data.get('status') == 'healthy':
                print_success("Database is healthy!")
                return True
            else:
                print_warning("Database is unhealthy")
                if 'database' in data and 'error' in data['database']:
                    print_error(f"Error: {data['database']['error']}")
                return False
        else:
            print_error(f"Database health check failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Is the server running?")
        return False
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_redis_health_check(base_url='http://localhost:8000'):
    """Test Redis health check endpoint."""
    print_header("Testing Redis Health Check (/health/redis/)")
    
    try:
        url = f"{base_url}/health/redis/"
        print_info(f"Testing: {url}")
        
        response = requests.get(url, timeout=5)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Redis health check endpoint is accessible")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Timestamp: {data.get('timestamp', 'unknown')}")
            
            if 'redis' in data:
                redis_info = data['redis']
                print_info("\nRedis Information:")
                print_info(f"  - URL: {redis_info.get('url', 'unknown')}")
                print_info(f"  - Response Time: {redis_info.get('response_time_ms', 0):.2f}ms")
                
                if 'server_info' in redis_info:
                    server_info = redis_info['server_info']
                    print_info("\nRedis Server Info:")
                    print_info(f"  - Version: {server_info.get('redis_version', 'unknown')}")
                    print_info(f"  - Connected Clients: {server_info.get('connected_clients', 0)}")
            
            if data.get('status') == 'healthy':
                print_success("Redis is healthy!")
                return True
            else:
                print_warning("Redis is unhealthy or not configured")
                if 'redis' in data and 'error' in data['redis']:
                    print_error(f"Error: {data['redis']['error']}")
                return False
        else:
            print_error(f"Redis health check failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Is the server running?")
        return False
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_nginx_health_checks(base_url='http://localhost'):
    """Test health checks through Nginx."""
    print_header("Testing Health Checks Through Nginx")
    
    results = []
    
    # Test overall health check through Nginx
    try:
        url = f"{base_url}/health/"
        print_info(f"Testing through Nginx: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_success("Nginx health check endpoint is accessible")
            results.append(True)
        else:
            print_warning(f"Nginx health check returned status {response.status_code}")
            results.append(False)
    except Exception as e:
        print_error(f"Could not test Nginx health check: {str(e)}")
        results.append(False)
    
    # Test database health check through Nginx
    try:
        url = f"{base_url}/health/db/"
        print_info(f"Testing through Nginx: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_success("Nginx database health check endpoint is accessible")
            results.append(True)
        else:
            print_warning(f"Nginx database health check returned status {response.status_code}")
            results.append(False)
    except Exception as e:
        print_error(f"Could not test Nginx database health check: {str(e)}")
        results.append(False)
    
    # Test Redis health check through Nginx
    try:
        url = f"{base_url}/health/redis/"
        print_info(f"Testing through Nginx: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code in [200, 503]:  # 503 is OK if Redis is not configured
            print_success("Nginx Redis health check endpoint is accessible")
            results.append(True)
        else:
            print_warning(f"Nginx Redis health check returned status {response.status_code}")
            results.append(False)
    except Exception as e:
        print_error(f"Could not test Nginx Redis health check: {str(e)}")
        results.append(False)
    
    return all(results)


def main():
    """Run all health check tests."""
    print_header("Health Check Endpoints Test Suite")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Django Settings: {settings.DJANGO_SETTINGS_MODULE}")
    print_info(f"Debug Mode: {settings.DEBUG}")
    
    # Determine base URL
    base_url = os.environ.get('BASE_URL', 'http://localhost:8000')
    nginx_url = os.environ.get('NGINX_URL', 'http://localhost')
    
    print_info(f"\nTesting against: {base_url}")
    print_info(f"Nginx URL: {nginx_url}")
    
    results = []
    
    # Test overall health check
    results.append(test_overall_health_check(base_url))
    
    # Test database health check
    results.append(test_database_health_check(base_url))
    
    # Test Redis health check
    results.append(test_redis_health_check(base_url))
    
    # Test through Nginx (if available)
    print_info("\nNote: Nginx tests require Nginx to be running on port 80")
    nginx_result = test_nginx_health_checks(nginx_url)
    results.append(nginx_result)
    
    # Summary
    print_header("Test Summary")
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print_info(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    if failed_tests > 0:
        print_error(f"Failed: {failed_tests}")
    
    if all(results):
        print_success("\n🎉 All health check tests passed!")
        return 0
    else:
        print_warning("\n⚠ Some health check tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

