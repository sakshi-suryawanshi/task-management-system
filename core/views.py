"""
Core views for the Task Management System.
"""

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import redis


def health_check(request):
    """
    Health check endpoint for Docker health checks.
    Returns 200 if all services are healthy.
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis connection
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if redis_url:
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            health_status['services']['redis'] = 'healthy'
        else:
            health_status['services']['redis'] = 'not configured'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        # Don't mark overall status as unhealthy for Redis in development
        if not settings.DEBUG:
            health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
