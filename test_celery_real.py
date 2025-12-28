#!/usr/bin/env python
"""
Quick test script to verify Celery tasks are working in real environment.

This script tests:
1. Celery connection
2. Task queuing
3. Task execution
4. Notification creation

Usage:
    # Make sure Celery worker is running first:
    docker-compose up celery
    
    # Then run this script:
    python test_celery_real.py
"""

import os
import sys
import django
import time

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from taskmanager.celery import app, debug_task
from notifications.tasks import create_notification, send_bulk_notifications
from notifications.models import Notification
from users.models import User


def print_separator(title):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_celery_connection():
    """Test if Celery can connect to Redis and worker is available."""
    print_separator("Testing Celery Connection")
    
    try:
        # Check if workers are active
        inspector = app.control.inspect()
        active_workers = inspector.active()
        
        if active_workers:
            print("✅ Celery workers are active!")
            for worker, tasks in active_workers.items():
                print(f"   Worker: {worker}")
                print(f"   Active tasks: {len(tasks)}")
            return True
        else:
            print("❌ No active Celery workers found!")
            print("   Please start Celery worker:")
            print("   docker-compose up celery")
            return False
    except Exception as e:
        print(f"❌ Error checking Celery connection: {e}")
        print("   Make sure Redis is running: docker-compose up redis")
        return False


def test_debug_task():
    """Test the debug task."""
    print_separator("Testing Debug Task")
    
    try:
        print("Queuing debug task...")
        result = debug_task.delay()
        print(f"✅ Task queued! Task ID: {result.id}")
        
        # Wait for task to complete
        print("Waiting for task to complete...")
        time.sleep(2)
        
        if result.ready():
            print("✅ Task completed successfully!")
            print(f"   Task state: {result.state}")
            return True
        else:
            print(f"⚠️  Task still pending. State: {result.state}")
            print("   This might mean worker is busy or not processing tasks")
            return False
    except Exception as e:
        print(f"❌ Error testing debug task: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_notification_task():
    """Test create_notification task."""
    print_separator("Testing create_notification Task")
    
    try:
        # Get a user
        user = User.objects.first()
        if not user:
            print("❌ No users found in database!")
            print("   Please create a user first")
            return False
        
        print(f"Using user: {user.username} (ID: {user.id})")
        
        # Get initial notification count
        initial_count = Notification.objects.filter(user=user).count()
        print(f"Initial notification count: {initial_count}")
        
        # Queue notification task
        print("Queuing notification task...")
        result = create_notification.delay(
            user_id=user.id,
            message="Test notification from Celery - " + str(time.time()),
            notification_type=Notification.TYPE_SYSTEM,
            metadata={'test': True, 'timestamp': time.time()}
        )
        print(f"✅ Task queued! Task ID: {result.id}")
        
        # Wait for task to complete
        print("Waiting for task to complete...")
        time.sleep(3)
        
        if result.ready():
            task_result = result.get()
            print(f"✅ Task completed! Result: {task_result}")
            
            # Check if notification was created
            final_count = Notification.objects.filter(user=user).count()
            print(f"Final notification count: {final_count}")
            
            if final_count > initial_count:
                notification = Notification.objects.filter(
                    user=user
                ).latest('created_at')
                print(f"✅ Notification created!")
                print(f"   ID: {notification.id}")
                print(f"   Message: {notification.message}")
                print(f"   Type: {notification.type}")
                return True
            else:
                print("⚠️  Notification count didn't increase")
                return False
        else:
            print(f"⚠️  Task still pending. State: {result.state}")
            return False
    except Exception as e:
        print(f"❌ Error testing create_notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_bulk_notifications():
    """Test send_bulk_notifications task."""
    print_separator("Testing send_bulk_notifications Task")
    
    try:
        # Get users
        users = User.objects.all()[:3]  # Get up to 3 users
        if not users:
            print("❌ No users found in database!")
            return False
        
        user_ids = [u.id for u in users]
        print(f"Using {len(user_ids)} users: {[u.username for u in users]}")
        
        # Get initial notification counts
        initial_counts = {u.id: Notification.objects.filter(user=u).count() for u in users}
        
        # Queue bulk notification task
        print("Queuing bulk notification task...")
        result = send_bulk_notifications.delay(
            user_ids=user_ids,
            message="Bulk test notification from Celery - " + str(time.time()),
            notification_type=Notification.TYPE_SYSTEM,
            metadata={'test': True, 'bulk': True}
        )
        print(f"✅ Task queued! Task ID: {result.id}")
        
        # Wait for task to complete
        print("Waiting for task to complete...")
        time.sleep(3)
        
        if result.ready():
            task_result = result.get()
            print(f"✅ Task completed! Result: {task_result}")
            
            # Check if notifications were created
            created_count = task_result.get('created_count', 0)
            failed_count = task_result.get('failed_count', 0)
            
            print(f"   Created: {created_count}")
            print(f"   Failed: {failed_count}")
            
            if created_count > 0:
                print("✅ Bulk notifications created successfully!")
                return True
            else:
                print("⚠️  No notifications were created")
                return False
        else:
            print(f"⚠️  Task still pending. State: {result.state}")
            return False
    except Exception as e:
        print(f"❌ Error testing send_bulk_notifications: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print_separator("Celery Real-World Test Suite")
    print("This script tests Celery tasks in a real environment.")
    print("Make sure Celery worker is running: docker-compose up celery\n")
    
    results = []
    
    # Test 1: Connection
    results.append(("Celery Connection", test_celery_connection()))
    
    if not results[0][1]:
        print("\n❌ Celery connection failed. Please start services:")
        print("   docker-compose up redis celery")
        sys.exit(1)
    
    # Test 2: Debug task
    results.append(("Debug Task", test_debug_task()))
    
    # Test 3: Create notification
    results.append(("Create Notification", test_create_notification_task()))
    
    # Test 4: Bulk notifications
    results.append(("Bulk Notifications", test_send_bulk_notifications()))
    
    # Summary
    print_separator("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Celery tests passed! Your setup is working correctly!")
        print("\nNext steps:")
        print("  1. Check Flower dashboard: http://localhost:5555")
        print("  2. Create a task in Django admin to see automatic notifications")
        print("  3. Check notification logs: docker-compose logs celery")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("\nTroubleshooting:")
        print("  1. Check Celery worker: docker-compose ps celery")
        print("  2. Check Celery logs: docker-compose logs celery")
        print("  3. Check Redis: docker-compose ps redis")
        print("  4. Restart services: docker-compose restart celery")
        sys.exit(1)


if __name__ == '__main__':
    main()

