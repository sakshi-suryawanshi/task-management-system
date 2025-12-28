"""
Celery configuration for taskmanager project.

This file configures Celery to work with Django and Redis.
It sets up the Celery application instance and ensures proper
task discovery from all Django apps.

Production-ready configuration with proper logging, error handling,
and task discovery mechanisms.
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

# Set the default Django settings module for the 'celery' program.
# This is important for Django apps that use Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')

# Create the Celery app instance
# The 'taskmanager' string is the main module name for this app
app = Celery('taskmanager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in Django settings.
# This allows us to use settings like CELERY_BROKER_URL in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
# This automatically discovers tasks in tasks.py files across all apps:
# - users/tasks.py
# - teams/tasks.py
# - projects/tasks.py
# - tasks/tasks.py
# - notifications/tasks.py
# - core/tasks.py
app.autodiscover_tasks()

# Configure logging for Celery
# This ensures Celery uses Django's logging configuration
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure Celery logging to use Django's logging configuration."""
    from django.conf import settings
    import logging.config
    logging.config.dictConfig(settings.LOGGING)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task to test Celery is working properly.
    
    This task can be used to verify:
    - Celery worker is running
    - Redis connection is working
    - Task execution is functional
    
    Usage:
        from taskmanager.celery import debug_task
        result = debug_task.delay()
        # Check task state
        print(result.state)  # Should be 'PENDING', then 'SUCCESS'
        # Note: Results are ignored (ignore_result=True), so result.get() won't return data
    
    Returns:
        str: Success message (result is not stored due to ignore_result=True)
    """
    logger = logging.getLogger(__name__)
    logger.info(f'Debug task executed: Request={self.request!r}')
    print(f'Debug task executed: Request={self.request!r}')
    return f'Task executed successfully: {self.request.id}'


# ============================================================================
# Celery Beat Schedule Configuration
# ============================================================================
# 
# This section configures periodic tasks that run on a schedule.
# Tasks are scheduled using crontab syntax for precise timing control.
#
# Schedule Format:
#   crontab(minute='*', hour='*', day_of_week='*', day_of_month='*', month_of_year='*')
#
# Examples:
#   - Daily at 9:00 AM: crontab(hour=9, minute=0)
#   - Every Monday at 9:00 AM: crontab(hour=9, minute=0, day_of_week=1)
#   - First day of month at 2:00 AM: crontab(hour=2, minute=0, day_of_month=1)
#   - Every Sunday at 2:00 AM: crontab(hour=2, minute=0, day_of_week=0)
#
# Note: Since we're using django-celery-beat with DatabaseScheduler,
# these schedules can also be managed dynamically via Django admin.
# However, defining them here provides a default configuration.
# ============================================================================

app.conf.beat_schedule = {
    # Daily Task Reminders
    # Runs every day at 9:00 AM to send reminders about tasks due today or overdue
    'send-daily-reminders': {
        'task': 'notifications.tasks.send_daily_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9:00 AM
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        },
    },
    
    # Weekly Digest Email
    # Runs every Monday at 9:00 AM to send weekly activity summary
    'send-weekly-digest': {
        'task': 'notifications.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Every Monday at 9:00 AM
        'options': {
            'expires': 7200,  # Task expires after 2 hours if not executed
        },
    },
    
    # Cleanup Old Notifications
    # Runs every Sunday at 2:00 AM to remove old read notifications
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2:00 AM
        'kwargs': {'days_old': 30},  # Delete notifications older than 30 days
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        },
    },
    
    # Archive Completed Projects
    # Runs on the first day of each month at 2:00 AM to archive old completed projects
    'archive-completed-projects': {
        'task': 'projects.tasks.archive_completed_projects',
        'schedule': crontab(hour=2, minute=0, day_of_month=1),  # First day of month at 2:00 AM
        'kwargs': {'days_since_completion': 90},  # Archive projects completed 90+ days ago
        'options': {
            'expires': 7200,  # Task expires after 2 hours if not executed
        },
    },
}

# Timezone for scheduled tasks
app.conf.timezone = 'UTC'

