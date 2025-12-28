#!/usr/bin/env python
"""
Manual test script for email tasks - runs tasks synchronously to see immediate results.

This script tests email tasks by calling them directly (not through Celery queue).
Use this to quickly verify tasks work without needing Celery worker running.
"""

import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from django.conf import settings
from users.models import User, UserProfile
from teams.models import Team, TeamMember
from projects.models import Project, ProjectMember
from tasks.models import Task

# Import tasks (call directly, not .delay())
from notifications.tasks import (
    send_welcome_email,
    send_task_assignment_email,
    send_task_due_reminder,
    send_project_update_email
)

print("=" * 80)
print("  MANUAL EMAIL TASKS TEST")
print("=" * 80)
print()

# Set console backend if not set
if not hasattr(settings, 'EMAIL_BACKEND') or settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    print("⚠️  Setting EMAIL_BACKEND to console for testing (emails will print to console)")
    print("   To use SMTP, configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
    print()
    # We'll set it in environment, but settings are already loaded
    # User should set it in .env or use: EMAIL_BACKEND=... python test_email_manual.py

# Get or create test user
print("Step 1: Getting or creating test user...")
try:
    test_user = User.objects.filter(email__icontains='test').first()
    if not test_user:
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Created test user: {test_user.email}")
    else:
        print(f"✅ Using existing user: {test_user.email}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Ensure profile exists with email notifications enabled
try:
    profile = test_user.profile
    # Enable email notifications for testing
    if not profile.email_notifications:
        profile.email_notifications = True
        profile.save()
        print(f"✅ Enabled email notifications for test user")
except UserProfile.DoesNotExist:
    profile = UserProfile.objects.create(user=test_user, email_notifications=True)
    print(f"✅ Created user profile with email notifications enabled")

print()

# Test 1: Welcome Email
print("=" * 80)
print("TEST 1: Welcome Email")
print("=" * 80)
try:
    result = send_welcome_email(test_user.id)
    print(f"Result: {result}")
    if result.get('status') == 'success':
        print("✅ Welcome email task completed successfully!")
    elif result.get('status') == 'skipped':
        print(f"⚠️  Skipped: {result.get('reason')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("-" * 80)
print()

# Create test data for other tests
print("Step 2: Getting or creating test data (team, project, task)...")
try:
    # Try to use existing data first to avoid signal issues
    # Team
    team = Team.objects.filter(name__icontains='Test').first()
    if team:
        print(f"✅ Using existing team: {team.name}")
    else:
        # Try to get any team
        team = Team.objects.first()
        if not team:
            print("⚠️  No teams found. Creating test team (may have signal issues)...")
            from django.db import transaction
            with transaction.atomic():
                team = Team.objects.create(name='Test Team', description='Test team')
            TeamMember.objects.create(team=team, user=test_user, role=TeamMember.ROLE_MEMBER)
            print("✅ Created test team")
        else:
            print(f"✅ Using existing team: {team.name}")
    
    # Project
    project = Project.objects.filter(team=team).first()
    if project:
        print(f"✅ Using existing project: {project.name}")
    else:
        print("⚠️  No projects found in team. Creating test project (may have signal issues)...")
        from django.db import transaction
        with transaction.atomic():
            project = Project.objects.create(
                name='Test Project',
                description='Test project for email testing',
                team=team,
                status=Project.STATUS_ACTIVE
            )
        ProjectMember.objects.create(project=project, user=test_user, role=ProjectMember.ROLE_MEMBER)
        print("✅ Created test project")
    
    # Task
    task = Task.objects.filter(project=project).first()
    if task:
        print(f"✅ Using existing task: {task.title}")
        # Update assignee if needed
        if task.assignee != test_user:
            task.assignee = test_user
            task.save(update_fields=['assignee'])
            print("✅ Updated task assignee")
    else:
        print("⚠️  No tasks found. Creating test task (may have signal issues)...")
        from django.db import transaction
        with transaction.atomic():
            task = Task.objects.create(
                title='Test Task',
                description='This is a test task for email notification',
                project=project,
                assignee=test_user,
                created_by=test_user,
                status=Task.STATUS_TODO,
                priority=Task.PRIORITY_HIGH,
                due_date=timezone.now() + timedelta(days=2)
            )
        print("✅ Created test task")
        
except Exception as e:
    print(f"❌ Error with test data: {e}")
    print("   Trying to continue with any existing data...")
    # Try to get any existing task
    task = Task.objects.filter(assignee=test_user).first()
    if not task:
        task = Task.objects.first()
    if task:
        project = task.project
        print(f"✅ Found existing task: {task.title}")
    else:
        print("❌ Cannot proceed without test data")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print()

# Test 2: Task Assignment Email
print("=" * 80)
print("TEST 2: Task Assignment Email")
print("=" * 80)
try:
    result = send_task_assignment_email(test_user.id, task.id, test_user.id)
    print(f"Result: {result}")
    if result.get('status') == 'success':
        print("✅ Task assignment email task completed successfully!")
    elif result.get('status') == 'skipped':
        print(f"⚠️  Skipped: {result.get('reason')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("-" * 80)
print()

# Test 3: Task Due Reminder
print("=" * 80)
print("TEST 3: Task Due Reminder")
print("=" * 80)
try:
    result = send_task_due_reminder(test_user.id, task.id, days_until_due=2)
    print(f"Result: {result}")
    if result.get('status') == 'success':
        print("✅ Task due reminder email task completed successfully!")
    elif result.get('status') == 'skipped':
        print(f"⚠️  Skipped: {result.get('reason')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("-" * 80)
print()

# Test 4: Project Update Email
print("=" * 80)
print("TEST 4: Project Update Email")
print("=" * 80)
try:
    result = send_project_update_email(
        test_user.id,
        project.id,
        update_type='status_change',
        update_description='Project status updated to Active for testing'
    )
    print(f"Result: {result}")
    if result.get('status') == 'success':
        print("✅ Project update email task completed successfully!")
    elif result.get('status') == 'skipped':
        print(f"⚠️  Skipped: {result.get('reason')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("  ALL TESTS COMPLETE")
print("=" * 80)
print()
print("Note: If you used console backend, check the console output above for email content.")
print("If you used SMTP backend, check the recipient email inbox.")
print()

