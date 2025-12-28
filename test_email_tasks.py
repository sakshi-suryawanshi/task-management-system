#!/usr/bin/env python
"""
Test script for email notification tasks.

This script tests all email notification Celery tasks to ensure they:
1. Can be queued successfully
2. Execute without errors
3. Send emails correctly (if email backend is configured)

Usage:
    # Test with actual email sending (requires email configuration)
    python test_email_tasks.py
    
    # Test in development (uses console backend)
    EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend python test_email_tasks.py
"""

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from users.models import User, UserProfile
from teams.models import Team, TeamMember
from projects.models import Project, ProjectMember
from tasks.models import Task
from notifications.tasks import (
    send_task_assignment_email,
    send_task_due_reminder,
    send_project_update_email,
    send_welcome_email
)
from django.conf import settings


def print_separator(title):
    """Print a visual separator with title."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_test_result(test_name, success, details=None):
    """Print test result in a formatted way."""
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   {details}")
    print()


def test_email_configuration():
    """Test if email configuration is properly set up."""
    print_separator("Testing Email Configuration")
    
    checks = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    }
    
    all_passed = True
    for key, value in checks.items():
        if not value:
            print(f"❌ {key} is not configured")
            all_passed = False
        else:
            print(f"✅ {key}: {value}")
    
    # Check if email credentials are set (optional for console backend)
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("\n⚠️  WARNING: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set")
            print("   Email sending will fail. Use console backend for testing:")
            print("   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend")
    
    print_test_result("Email Configuration", all_passed)
    return all_passed


def create_test_data():
    """Create test data for email tasks."""
    print_separator("Creating Test Data")
    
    # Create or get test users
    try:
        test_user = User.objects.get(username='testuser')
        print("✅ Using existing test user")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print("✅ Created test user")
    
    try:
        assigner = User.objects.get(username='assigner')
        print("✅ Using existing assigner user")
    except User.DoesNotExist:
        assigner = User.objects.create_user(
            username='assigner',
            email='assigner@example.com',
            password='testpass123',
            first_name='Task',
            last_name='Assigner'
        )
        print("✅ Created assigner user")
    
    # Create user profile if it doesn't exist
    try:
        profile = test_user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=test_user,
            email_notifications=True
        )
        print("✅ Created user profile")
    
    # Create test team
    try:
        team = Team.objects.get(name='Test Team')
        print("✅ Using existing test team")
    except Team.DoesNotExist:
        team = Team.objects.create(
            name='Test Team',
            description='Test team for email task testing'
        )
        # Add users to team
        TeamMember.objects.create(team=team, user=test_user, role=TeamMember.ROLE_MEMBER)
        TeamMember.objects.create(team=team, user=assigner, role=TeamMember.ROLE_OWNER)
        print("✅ Created test team")
    
    # Create test project
    try:
        project = Project.objects.get(name='Test Project', team=team)
        print("✅ Using existing test project")
    except Project.DoesNotExist:
        project = Project.objects.create(
            name='Test Project',
            description='Test project for email task testing',
            team=team,
            status=Project.STATUS_ACTIVE,
            priority=Project.PRIORITY_HIGH
        )
        # Add users to project
        ProjectMember.objects.create(project=project, user=test_user, role=ProjectMember.ROLE_MEMBER)
        ProjectMember.objects.create(project=project, user=assigner, role=ProjectMember.ROLE_OWNER)
        print("✅ Created test project")
    
    # Create test task
    try:
        task = Task.objects.get(title='Test Task', project=project)
        task.assignee = test_user
        task.due_date = timezone.now() + timedelta(days=2)
        task.save()
        print("✅ Updated existing test task")
    except Task.DoesNotExist:
        task = Task.objects.create(
            title='Test Task',
            description='This is a test task for email notification testing',
            project=project,
            assignee=test_user,
            created_by=assigner,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_HIGH,
            due_date=timezone.now() + timedelta(days=2)
        )
        print("✅ Created test task")
    
    print_test_result("Test Data Creation", True)
    return test_user, assigner, project, task


def test_send_welcome_email(user):
    """Test send_welcome_email task."""
    print_separator("Testing send_welcome_email Task")
    
    try:
        # Call task synchronously for testing
        result = send_welcome_email(user.id)
        
        if result.get('status') == 'success':
            print_test_result("send_welcome_email", True, f"Email sent to {result.get('email')}")
            return True
        elif result.get('status') == 'skipped':
            print_test_result("send_welcome_email", True, f"Skipped: {result.get('reason')}")
            return True
        else:
            print_test_result("send_welcome_email", False, f"Error: {result.get('error')}")
            return False
    except Exception as e:
        print_test_result("send_welcome_email", False, f"Exception: {str(e)}")
        return False


def test_send_task_assignment_email(user, task, assigner):
    """Test send_task_assignment_email task."""
    print_separator("Testing send_task_assignment_email Task")
    
    try:
        # Call task synchronously for testing
        result = send_task_assignment_email(user.id, task.id, assigner.id)
        
        if result.get('status') == 'success':
            print_test_result("send_task_assignment_email", True, f"Email sent to {result.get('email')}")
            return True
        elif result.get('status') == 'skipped':
            print_test_result("send_task_assignment_email", True, f"Skipped: {result.get('reason')}")
            return True
        else:
            print_test_result("send_task_assignment_email", False, f"Error: {result.get('error')}")
            return False
    except Exception as e:
        print_test_result("send_task_assignment_email", False, f"Exception: {str(e)}")
        return False


def test_send_task_due_reminder(user, task):
    """Test send_task_due_reminder task."""
    print_separator("Testing send_task_due_reminder Task")
    
    try:
        # Call task synchronously for testing
        result = send_task_due_reminder(user.id, task.id, days_until_due=2)
        
        if result.get('status') == 'success':
            is_overdue = result.get('is_overdue', False)
            status_msg = "overdue" if is_overdue else "due soon"
            print_test_result("send_task_due_reminder", True, f"Email sent ({status_msg})")
            return True
        elif result.get('status') == 'skipped':
            print_test_result("send_task_due_reminder", True, f"Skipped: {result.get('reason')}")
            return True
        else:
            print_test_result("send_task_due_reminder", False, f"Error: {result.get('error')}")
            return False
    except Exception as e:
        print_test_result("send_task_due_reminder", False, f"Exception: {str(e)}")
        return False


def test_send_project_update_email(user, project):
    """Test send_project_update_email task."""
    print_separator("Testing send_project_update_email Task")
    
    try:
        # Call task synchronously for testing
        result = send_project_update_email(
            user.id,
            project.id,
            update_type='status_change',
            update_description='Project status has been updated to Active'
        )
        
        if result.get('status') == 'success':
            print_test_result("send_project_update_email", True, f"Email sent to {result.get('email')}")
            return True
        elif result.get('status') == 'skipped':
            print_test_result("send_project_update_email", True, f"Skipped: {result.get('reason')}")
            return True
        else:
            print_test_result("send_project_update_email", False, f"Error: {result.get('error')}")
            return False
    except Exception as e:
        print_test_result("send_project_update_email", False, f"Exception: {str(e)}")
        return False


def main():
    """Main test function."""
    print_separator("Email Notification Tasks Test Suite")
    print("This script tests all email notification Celery tasks.")
    print("Note: Use console email backend for testing without actual email sending:")
    print("EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend python test_email_tasks.py\n")
    
    # Test email configuration
    if not test_email_configuration():
        print("❌ Email configuration test failed. Please check your settings.")
        sys.exit(1)
    
    # Create test data
    try:
        test_user, assigner, project, task = create_test_data()
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        sys.exit(1)
    
    # Test all email tasks
    results = []
    
    results.append(("Welcome Email", test_send_welcome_email(test_user)))
    results.append(("Task Assignment Email", test_send_task_assignment_email(test_user, task, assigner)))
    results.append(("Task Due Reminder", test_send_task_due_reminder(test_user, task)))
    results.append(("Project Update Email", test_send_project_update_email(test_user, project)))
    
    # Print summary
    print_separator("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All email task tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()

