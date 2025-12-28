"""
Django project package initialization.

This module ensures that the Celery app is imported when Django starts,
which allows the @shared_task decorator to use this app instance.

This is required for Celery to work properly with Django.
The celery_app is imported here so it's available when Django loads.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)

