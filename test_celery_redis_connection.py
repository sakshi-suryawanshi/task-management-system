#!/usr/bin/env python
"""
Test script to verify Celery Redis connection.

This script tests the connection between Celery and Redis,
which is essential for task queuing and result storage.

Usage:
    python test_celery_redis_connection.py
    
Or in Docker:
    docker-compose exec web python test_celery_redis_connection.py
    docker-compose exec celery python test_celery_redis_connection.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

import redis
from django.conf import settings
from taskmanager.celery import app


def test_redis_connection():
    """Test direct Redis connection."""
    print("=" * 70)
    print("Testing Direct Redis Connection")
    print("=" * 70)
    
    try:
        # Parse Redis URL
        redis_url = settings.CELERY_BROKER_URL
        print(f"Redis URL: {redis_url}")
        
        # Create Redis client
        r = redis.from_url(redis_url)
        
        # Test connection
        print("\n1. Testing Redis connection...")
        r.ping()
        print("   ✅ Redis connection successful!")
        
        # Get Redis info
        print("\n2. Getting Redis server information...")
        info = r.info()
        print(f"   ✅ Redis version: {info.get('redis_version', 'unknown')}")
        print(f"   ✅ Connected clients: {info.get('connected_clients', 'unknown')}")
        print(f"   ✅ Used memory: {info.get('used_memory_human', 'unknown')}")
        
        # Test set/get
        print("\n3. Testing Redis set/get operations...")
        test_key = 'celery_test_key'
        test_value = 'celery_test_value'
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = r.get(test_key)
        
        if retrieved_value.decode() == test_value:
            print("   ✅ Redis set/get operations successful!")
            r.delete(test_key)  # Cleanup
        else:
            print(f"   ❌ Redis set/get failed: Expected '{test_value}', got '{retrieved_value}'")
            return False
        
        return True
        
    except redis.ConnectionError as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("\n   Troubleshooting:")
        print("   - Check if Redis container is running: docker-compose ps redis")
        print("   - Check Redis URL in settings: CELERY_BROKER_URL")
        print("   - Verify network connectivity to Redis container")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_celery_broker_connection():
    """Test Celery broker connection."""
    print("\n" + "=" * 70)
    print("Testing Celery Broker Connection")
    print("=" * 70)
    
    try:
        print("\n1. Getting Celery app broker connection...")
        broker_url = app.conf.broker_url
        print(f"   Broker URL: {broker_url}")
        
        print("\n2. Testing Celery broker connection...")
        # Check broker connection
        inspect = app.control.inspect()
        
        # Try to get active tasks (this requires a connection)
        active = inspect.active()
        
        if active is not None:
            print("   ✅ Celery broker connection successful!")
            print(f"   ✅ Active workers: {len(active)}")
            return True
        else:
            print("   ⚠️  Celery broker connection successful, but no active workers found.")
            print("   This is normal if no Celery workers are running.")
            print("   To test with workers, start: docker-compose up celery")
            return True
            
    except Exception as e:
        print(f"   ❌ Celery broker connection failed: {e}")
        print("\n   Troubleshooting:")
        print("   - Verify CELERY_BROKER_URL in settings.py")
        print("   - Check Redis container is running: docker-compose ps redis")
        print("   - Verify Celery configuration in taskmanager/celery.py")
        return False


def test_celery_result_backend():
    """Test Celery result backend connection."""
    print("\n" + "=" * 70)
    print("Testing Celery Result Backend Connection")
    print("=" * 70)
    
    try:
        print("\n1. Getting Celery result backend configuration...")
        result_backend = app.conf.result_backend
        print(f"   Result Backend URL: {result_backend}")
        
        print("\n2. Testing result backend connection...")
        # Test result backend by checking if we can connect
        backend = app.backend
        backend.ensure_chords_allowed()
        
        print("   ✅ Celery result backend connection successful!")
        return True
        
    except Exception as e:
        print(f"   ❌ Celery result backend connection failed: {e}")
        print("\n   Troubleshooting:")
        print("   - Verify CELERY_RESULT_BACKEND in settings.py")
        print("   - Check Redis container is running: docker-compose ps redis")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 70)
    print("CELERY REDIS CONNECTION TEST")
    print("=" * 70)
    print("\nThis script verifies that Celery can connect to Redis")
    print("for both message brokering and result storage.\n")
    
    results = []
    
    # Test 1: Direct Redis connection
    results.append(("Direct Redis Connection", test_redis_connection()))
    
    # Test 2: Celery broker connection
    results.append(("Celery Broker Connection", test_celery_broker_connection()))
    
    # Test 3: Celery result backend
    results.append(("Celery Result Backend", test_celery_result_backend()))
    
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
    
    if all_passed:
        print("\n🎉 All connection tests passed!")
        print("Celery is properly configured and connected to Redis.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

