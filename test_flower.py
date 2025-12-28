#!/usr/bin/env python
"""
Test script to verify Flower (Celery Monitoring Dashboard) is working.

This script tests:
1. Flower service accessibility
2. Flower API endpoints
3. Worker visibility in Flower
4. Task history visibility

Usage:
    # Make sure Flower is running first:
    docker-compose up -d flower
    
    # Then run this script:
    python test_flower.py
"""

import os
import sys
import requests
import time
import json

# Setup Django environment (for accessing Celery app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')

try:
    import django
    django.setup()
    from taskmanager.celery import app, debug_task
except ImportError:
    print("Warning: Django not available. Some tests will be skipped.")


def print_separator(title):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_success(message):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message):
    """Print error message."""
    print(f"❌ {message}")


def print_info(message):
    """Print info message."""
    print(f"ℹ️  {message}")


def test_flower_accessibility():
    """Test if Flower dashboard is accessible."""
    print_separator("Testing Flower Accessibility")
    
    flower_url = os.getenv('FLOWER_URL', 'http://localhost:5555')
    
    try:
        response = requests.get(flower_url, timeout=5)
        if response.status_code == 200:
            print_success(f"Flower dashboard is accessible at {flower_url}")
            return True
        else:
            print_error(f"Flower returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Flower at {flower_url}")
        print_info("Make sure Flower service is running: docker-compose up -d flower")
        return False
    except requests.exceptions.Timeout:
        print_error(f"Connection to Flower timed out")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_flower_api_workers():
    """Test Flower API to get worker information."""
    print_separator("Testing Flower API - Workers")
    
    flower_url = os.getenv('FLOWER_URL', 'http://localhost:5555')
    api_url = f"{flower_url}/api/workers"
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            workers = response.json()
            worker_count = len(workers)
            print_success(f"Flower API is accessible. Found {worker_count} worker(s)")
            
            if worker_count > 0:
                print_info("Active workers:")
                for worker_name, worker_info in workers.items():
                    print(f"  - {worker_name}")
                    if 'status' in worker_info:
                        print(f"    Status: {worker_info['status']}")
            else:
                print_info("No workers found. Make sure Celery worker is running.")
            return True
        else:
            print_error(f"Flower API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Flower API at {api_url}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response from Flower API")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_flower_api_tasks():
    """Test Flower API to get task information."""
    print_separator("Testing Flower API - Tasks")
    
    flower_url = os.getenv('FLOWER_URL', 'http://localhost:5555')
    api_url = f"{flower_url}/api/tasks"
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            tasks = response.json()
            task_count = len(tasks)
            print_success(f"Flower API tasks endpoint is accessible. Found {task_count} task(s) in history")
            return True
        else:
            print_error(f"Flower API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Flower API at {api_url}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response from Flower API")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False


def test_celery_integration():
    """Test if Celery tasks are visible in Flower."""
    print_separator("Testing Celery Integration with Flower")
    
    try:
        # Check if Celery app is available
        inspector = app.control.inspect()
        active_workers = inspector.active()
        
        if active_workers:
            print_success(f"Celery workers are active. Found {len(active_workers)} worker(s)")
            
            # Try to queue a test task
            print_info("Queuing a test task...")
            result = debug_task.delay()
            
            # Wait a bit for task to complete
            time.sleep(2)
            
            if result.ready():
                print_success(f"Test task completed. Task ID: {result.id}")
                
                # Check if task is visible in Flower
                flower_url = os.getenv('FLOWER_URL', 'http://localhost:5555')
                task_url = f"{flower_url}/api/task/info/{result.id}"
                
                try:
                    response = requests.get(task_url, timeout=5)
                    if response.status_code == 200:
                        task_info = response.json()
                        print_success(f"Task is visible in Flower: {task_info.get('name', 'N/A')}")
                        print_info(f"Task state: {task_info.get('state', 'N/A')}")
                        return True
                    else:
                        print_error(f"Could not fetch task info from Flower. Status: {response.status_code}")
                        return False
                except Exception as e:
                    print_error(f"Error fetching task from Flower: {str(e)}")
                    return False
            else:
                print_error("Test task did not complete in time")
                return False
        else:
            print_error("No active Celery workers found")
            print_info("Make sure Celery worker is running: docker-compose up -d celery")
            return False
            
    except NameError:
        print_error("Celery app not available (Django not set up)")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_flower_dashboard_features():
    """Test various Flower dashboard features."""
    print_separator("Testing Flower Dashboard Features")
    
    flower_url = os.getenv('FLOWER_URL', 'http://localhost:5555')
    
    endpoints_to_test = [
        ('/', 'Dashboard home'),
        ('/api/stats', 'Statistics'),
        ('/api/workers', 'Workers list'),
        ('/api/tasks', 'Tasks list'),
    ]
    
    results = []
    for endpoint, description in endpoints_to_test:
        url = f"{flower_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{description} endpoint is accessible")
                results.append(True)
            else:
                print_error(f"{description} endpoint returned status {response.status_code}")
                results.append(False)
        except Exception as e:
            print_error(f"{description} endpoint error: {str(e)}")
            results.append(False)
    
    return all(results)


def main():
    """Run all Flower tests."""
    print("\n" + "=" * 80)
    print("  FLOWER MONITORING DASHBOARD - TEST SUITE")
    print("=" * 80 + "\n")
    
    print_info("Flower URL: http://localhost:5555 (or set FLOWER_URL environment variable)")
    print_info("Make sure Flower service is running: docker-compose up -d flower")
    print_info("Make sure Celery worker is running: docker-compose up -d celery\n")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # Run tests
    tests = [
        ('Flower Accessibility', test_flower_accessibility),
        ('Flower API - Workers', test_flower_api_workers),
        ('Flower API - Tasks', test_flower_api_tasks),
        ('Celery Integration', test_celery_integration),
        ('Dashboard Features', test_flower_dashboard_features),
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                results['passed'] += 1
                results['tests'].append((test_name, True))
            else:
                results['failed'] += 1
                results['tests'].append((test_name, False))
        except Exception as e:
            print_error(f"Test '{test_name}' raised exception: {str(e)}")
            results['failed'] += 1
            results['tests'].append((test_name, False))
    
    # Print summary
    print_separator("Test Summary")
    total = results['passed'] + results['failed']
    print(f"Total Tests: {total}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    
    print("\n" + "=" * 80)
    print("  DETAILED RESULTS")
    print("=" * 80 + "\n")
    
    for test_name, passed in results['tests']:
        if passed:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print("\n" + "=" * 80)
    if results['failed'] == 0:
        print("  ✅ ALL TESTS PASSED")
        print("=" * 80 + "\n")
        print_info("Flower is working correctly!")
        print_info("Access the dashboard at: http://localhost:5555")
        return 0
    else:
        print("  ⚠️  SOME TESTS FAILED")
        print("=" * 80 + "\n")
        print_info("Please check the errors above and ensure:")
        print_info("1. Flower service is running: docker-compose up -d flower")
        print_info("2. Celery worker is running: docker-compose up -d celery")
        print_info("3. Redis is running: docker-compose up -d redis")
        print_info("4. Check logs: docker-compose logs flower")
        return 1


if __name__ == '__main__':
    sys.exit(main())

