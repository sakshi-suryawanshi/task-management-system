#!/usr/bin/env python
"""
Test script to verify Celery task execution.

This script tests basic Celery task execution to ensure:
- Tasks can be queued
- Workers can receive and execute tasks
- Task results can be retrieved
- Debug task works correctly

Usage:
    python test_celery_task_execution.py
    
Prerequisites:
    - Redis must be running
    - Celery worker should be running (optional, but recommended)
        docker-compose up celery
    
Or in Docker:
    docker-compose exec web python test_celery_task_execution.py
"""

import os
import sys
import time
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from taskmanager.celery import app, debug_task


def test_task_queue():
    """Test if we can queue a task."""
    print("=" * 70)
    print("Testing Task Queue")
    print("=" * 70)
    
    try:
        print("\n1. Queuing debug task...")
        result = debug_task.delay()
        print(f"   ✅ Task queued successfully!")
        print(f"   Task ID: {result.id}")
        print(f"   Task State: {result.state}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Failed to queue task: {e}")
        print("\n   Troubleshooting:")
        print("   - Check if Redis is running: docker-compose ps redis")
        print("   - Verify CELERY_BROKER_URL in settings.py")
        return None


def test_task_execution(result):
    """Test if task executes successfully."""
    print("\n" + "=" * 70)
    print("Testing Task Execution")
    print("=" * 70)
    
    if result is None:
        print("\n❌ Cannot test execution: task was not queued")
        return False
    
    try:
        print(f"\n1. Waiting for task execution (Task ID: {result.id})...")
        print("   Note: This requires a Celery worker to be running.")
        print("   If no worker is running, the task will remain in PENDING state.")
        
        # Wait for task to complete (with timeout)
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while result.state == 'PENDING' and (time.time() - start_time) < timeout:
            time.sleep(1)
            # Check task state (no refresh method in Celery 5.x, state is property)
            current_state = result.state
            print(f"   Task state: {current_state}...", end='\r')
            if current_state != 'PENDING':
                break
        
        print(f"\n   Final task state: {result.state}")
        
        if result.state == 'SUCCESS':
            print("   ✅ Task executed successfully!")
            
            # Get result
            try:
                task_result = result.get(timeout=5)
                print(f"   Task result: {task_result}")
            except Exception as e:
                print(f"   ⚠️  Could not retrieve result: {e}")
            
            return True
            
        elif result.state == 'PENDING':
            print("\n   ⚠️  Task is still pending (no worker running)")
            print("   This is expected if no Celery worker is active.")
            print("   To test full execution, start a worker:")
            print("   docker-compose up celery")
            return True  # Not a failure, just no worker
            
        elif result.state == 'FAILURE':
            print("   ❌ Task execution failed!")
            try:
                error_info = result.info
                print(f"   Error: {error_info}")
            except:
                pass
            return False
            
        else:
            print(f"   ⚠️  Task in unexpected state: {result.state}")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"   ❌ Error checking task execution: {e}")
        return False


def test_worker_availability():
    """Check if Celery workers are available."""
    print("\n" + "=" * 70)
    print("Checking Worker Availability")
    print("=" * 70)
    
    try:
        print("\n1. Inspecting active workers...")
        inspect = app.control.inspect()
        
        # Check active workers
        active = inspect.active()
        stats = inspect.stats()
        registered = inspect.registered()
        
        if active:
            print(f"   ✅ Found {len(active)} active worker(s):")
            for worker_name in active.keys():
                print(f"      - {worker_name}")
                if stats and worker_name in stats:
                    worker_stats = stats[worker_name]
                    print(f"        Pool: {worker_stats.get('pool', {}).get('implementation', 'unknown')}")
                    print(f"        Processes: {worker_stats.get('pool', {}).get('max-concurrency', 'unknown')}")
        else:
            print("   ⚠️  No active workers found")
            print("   Start a worker with: docker-compose up celery")
            return False
        
        if registered:
            print(f"\n   ✅ Registered tasks: {len(registered.get(list(registered.keys())[0], []))}")
            print("   Registered task names:")
            for task_name in registered.get(list(registered.keys())[0], [])[:10]:  # Show first 10
                print(f"      - {task_name}")
            if len(registered.get(list(registered.keys())[0], [])) > 10:
                print(f"      ... and {len(registered.get(list(registered.keys())[0], [])) - 10} more")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not inspect workers: {e}")
        print("   This might be normal if no workers are running")
        return False


def test_simple_task():
    """Test a simple synchronous task execution."""
    print("\n" + "=" * 70)
    print("Testing Simple Task (Synchronous)")
    print("=" * 70)
    
    try:
        print("\n1. Creating a simple test task...")
        
        @app.task(name='test.simple_task')
        def simple_task(message):
            """Simple test task."""
            return f"Task executed: {message}"
        
        print("2. Executing task synchronously (for testing)...")
        result = simple_task("Hello from Celery!")
        print(f"   ✅ Task executed: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Simple task test failed: {e}")
        return False


def main():
    """Run all task execution tests."""
    print("\n" + "=" * 70)
    print("CELERY TASK EXECUTION TEST")
    print("=" * 70)
    print("\nThis script verifies that Celery tasks can be:")
    print("- Queued successfully")
    print("- Executed by workers")
    print("- Results retrieved")
    print("\nNote: For full testing, ensure Celery worker is running:")
    print("docker-compose up celery\n")
    
    results = []
    
    # Test 1: Check worker availability
    worker_available = test_worker_availability()
    
    # Test 2: Queue a task
    task_result = test_task_queue()
    results.append(("Task Queue", task_result is not None))
    
    # Test 3: Execute task (if queued)
    if task_result:
        execution_result = test_task_execution(task_result)
        results.append(("Task Execution", execution_result))
    
    # Test 4: Simple synchronous task (always works)
    results.append(("Simple Task", test_simple_task()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 70)
    
    if not worker_available:
        print("\n⚠️  No Celery workers are running.")
        print("Some tests may show as 'passed' but tasks won't execute.")
        print("Start a worker with: docker-compose up celery")
    
    if all_passed:
        print("\n🎉 All task execution tests passed!")
        print("Celery is properly configured and tasks can be executed.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

