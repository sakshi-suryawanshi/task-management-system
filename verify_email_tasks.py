#!/usr/bin/env python
"""
Quick verification script to check if email tasks can be imported and templates exist.

This script performs basic checks without requiring database or Celery setup.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {e}")
    sys.exit(1)

print("✅ Django setup successful")

# Check imports
try:
    from notifications.tasks import (
        send_task_assignment_email,
        send_task_due_reminder,
        send_project_update_email,
        send_welcome_email,
        should_send_email,
        send_email_with_html
    )
    print("✅ All task functions imported successfully")
except ImportError as e:
    print(f"❌ Failed to import tasks: {e}")
    sys.exit(1)

# Check template loading
from django.template.loader import render_to_string
from django.conf import settings

templates_to_check = [
    'notifications/emails/base.html',
    'notifications/emails/task_assignment.html',
    'notifications/emails/task_assignment.txt',
    'notifications/emails/task_due_reminder.html',
    'notifications/emails/task_due_reminder.txt',
    'notifications/emails/project_update.html',
    'notifications/emails/project_update.txt',
    'notifications/emails/welcome.html',
    'notifications/emails/welcome.txt',
]

print("\nChecking templates...")
all_templates_found = True
for template_path in templates_to_check:
    try:
        # Try to load template with minimal context
        context = {
            'site_name': 'Test Site',
            'user': None,
            'task': None,
            'project': None,
        }
        render_to_string(template_path, context)
        print(f"✅ Template found: {template_path}")
    except Exception as e:
        print(f"❌ Template not found or error: {template_path} - {e}")
        all_templates_found = False

if all_templates_found:
    print("\n✅ All templates found and can be loaded")
else:
    print("\n❌ Some templates failed to load")
    sys.exit(1)

# Check settings
print("\nChecking email settings...")
email_settings = {
    'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', None),
    'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', None),
    'SITE_NAME': getattr(settings, 'SITE_NAME', None),
    'FRONTEND_URL': getattr(settings, 'FRONTEND_URL', None),
}

for key, value in email_settings.items():
    if value:
        print(f"✅ {key}: {value}")
    else:
        print(f"⚠️  {key}: Not set (will use default)")

print("\n🎉 All basic checks passed!")
print("\nTo test email tasks with actual sending:")
print("1. Configure EMAIL_BACKEND in .env file")
print("2. Run: python test_email_tasks.py")
print("\nOr use console backend for testing:")
print("EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend python test_email_tasks.py")

