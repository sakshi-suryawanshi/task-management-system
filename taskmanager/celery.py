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

