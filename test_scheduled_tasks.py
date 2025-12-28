"""
Test script for scheduled Celery Beat tasks (Task 5.5).

This script tests all scheduled tasks:
1. send_daily_reminders
2. send_weekly_digest
3. cleanup_old_notifications
4. archive_completed_projects

Usage:
    python test_scheduled_tasks.py
    OR
    docker-compose exec web python test_scheduled_tasks.py
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from users.models import User
from tasks.models import Task
from projects.models import Project
from notifications.models import Notification
from notifications.tasks import (
    send_daily_reminders,
    send_weekly_digest,
    cleanup_old_notifications
)
from projects.tasks import archive_completed_projects


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_send_daily_reminders():
    """Test the send_daily_reminders task."""
    print_section("Testing: send_daily_reminders")
    
    try:
        # Call the task directly (synchronous for testing)
        result = send_daily_reminders()
        
        print(f"✅ Task executed successfully!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Users notified: {result.get('total_users_notified', 0)}")
        print(f"   Tasks due today: {result.get('tasks_due_today', 0)}")
        print(f"   Overdue tasks: {result.get('overdue_tasks', 0)}")
        print(f"   Upcoming tasks: {result.get('upcoming_tasks', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_weekly_digest():
    """Test the send_weekly_digest task."""
    print_section("Testing: send_weekly_digest")
    
    try:
        # Call the task directly (synchronous for testing)
        result = send_weekly_digest()
        
        print(f"✅ Task executed successfully!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Users notified: {result.get('total_users_notified', 0)}")
        print(f"   Tasks completed: {result.get('total_tasks_completed', 0)}")
        print(f"   Tasks created: {result.get('total_tasks_created', 0)}")
        print(f"   Active projects: {result.get('total_projects_active', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cleanup_old_notifications():
    """Test the cleanup_old_notifications task."""
    print_section("Testing: cleanup_old_notifications")
    
    try:
        # Count notifications before cleanup
        total_before = Notification.objects.count()
        read_before = Notification.objects.filter(read=True).count()
        
        print(f"   Notifications before cleanup:")
        print(f"   - Total: {total_before}")
        print(f"   - Read: {read_before}")
        
        # Call the task with 30 days (default)
        result = cleanup_old_notifications(days_old=30)
        
        # Count notifications after cleanup
        total_after = Notification.objects.count()
        read_after = Notification.objects.filter(read=True).count()
        
        print(f"✅ Task executed successfully!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Notifications deleted: {result.get('notifications_deleted', 0)}")
        print(f"   Days old threshold: {result.get('days_old', 0)}")
        print(f"   Cutoff date: {result.get('cutoff_date', 'N/A')}")
        print(f"\n   Notifications after cleanup:")
        print(f"   - Total: {total_after}")
        print(f"   - Read: {read_after}")
        print(f"   - Deleted: {total_before - total_after}")
        
        return True
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_archive_completed_projects():
    """Test the archive_completed_projects task."""
    print_section("Testing: archive_completed_projects")
    
    try:
        # Count completed projects before archiving
        completed_before = Project.objects.filter(
            status=Project.STATUS_COMPLETED
        ).count()
        
        print(f"   Completed projects before archiving: {completed_before}")
        
        # Call the task with 90 days (default)
        result = archive_completed_projects(days_since_completion=90)
        
        print(f"✅ Task executed successfully!")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Projects archived: {result.get('projects_archived', 0)}")
        print(f"   Projects checked: {result.get('projects_checked', 0)}")
        print(f"   Days since completion threshold: {result.get('days_since_completion', 0)}")
        print(f"   Cutoff date: {result.get('cutoff_date', 'N/A')}")
        
        archived_ids = result.get('archived_project_ids', [])
        if archived_ids:
            print(f"   Archived project IDs: {archived_ids}")
        
        return True
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_celery_beat_schedule():
    """Verify Celery Beat schedule configuration."""
    print_section("Verifying: Celery Beat Schedule Configuration")
    
    try:
        from taskmanager.celery import app
        
        # Check if beat_schedule is configured
        beat_schedule = app.conf.beat_schedule
        
        if not beat_schedule:
            print("❌ No beat schedule configured!")
            return False
        
        print(f"✅ Beat schedule configured with {len(beat_schedule)} tasks:\n")
        
        expected_tasks = [
            'send-daily-reminders',
            'send-weekly-digest',
            'cleanup-old-notifications',
            'archive-completed-projects'
        ]
        
        for task_name in expected_tasks:
            if task_name in beat_schedule:
                schedule = beat_schedule[task_name]
                print(f"   ✅ {task_name}")
                print(f"      Task: {schedule.get('task', 'N/A')}")
                print(f"      Schedule: {schedule.get('schedule', 'N/A')}")
                if 'kwargs' in schedule:
                    print(f"      Arguments: {schedule['kwargs']}")
                print()
            else:
                print(f"   ❌ {task_name} - NOT FOUND IN SCHEDULE!")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error verifying schedule: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  SCHEDULED TASKS TEST SUITE (Task 5.5)")
    print("=" * 70)
    
    results = []
    
    # Verify schedule configuration first
    results.append(("Schedule Configuration", verify_celery_beat_schedule()))
    
    # Test each scheduled task
    results.append(("send_daily_reminders", test_send_daily_reminders()))
    results.append(("send_weekly_digest", test_send_weekly_digest()))
    results.append(("cleanup_old_notifications", test_cleanup_old_notifications()))
    results.append(("archive_completed_projects", test_archive_completed_projects()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 All tests passed! Task 5.5 is complete.")
        return 0
    else:
        print(f"\n   ⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

