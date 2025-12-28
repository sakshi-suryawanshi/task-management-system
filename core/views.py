"""
Core views for the Task Management System.

This module contains health check endpoints for monitoring the application
and its dependencies (database, Redis).
"""

import time
from django.db import connection
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import redis
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Comprehensive health check endpoint.
    
    Checks the overall health of the application including:
    - Database connectivity
    - Redis connectivity
    - Application status
    
    Returns 200 if all critical services are healthy, 503 otherwise.
    This endpoint is used by Docker health checks, load balancers, and monitoring systems.
    """
    
    permission_classes = [AllowAny]  # Health checks should be publicly accessible

    @extend_schema(
        tags=['Health'],
        summary='Overall health check',
        description="""
        Check the overall health status of the application and all its dependencies.
        
        This endpoint performs health checks on:
        - **Database**: Verifies MySQL connection and basic query execution
        - **Redis**: Verifies Redis connection and ping response
        
        **Response Codes:**
        - `200 OK`: All services are healthy
        - `503 Service Unavailable`: One or more services are unhealthy
        
        **Use Cases:**
        - Docker health checks
        - Load balancer health monitoring
        - Kubernetes liveness/readiness probes
        - Monitoring system checks
        - CI/CD pipeline health verification
        
        **Note:** This endpoint does not require authentication.
        """,
        responses={
            200: {
                'description': 'All services are healthy',
                'examples': [
                    OpenApiExample(
                        'Healthy Response',
                        value={
                            'status': 'healthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'version': '1.0.0',
                            'services': {
                                'database': {
                                    'status': 'healthy',
                                    'response_time_ms': 2.5,
                                },
                                'redis': {
                                    'status': 'healthy',
                                    'response_time_ms': 1.2,
                                },
                            },
                        },
                    ),
                ],
            },
            503: {
                'description': 'One or more services are unhealthy',
                'examples': [
                    OpenApiExample(
                        'Unhealthy Response',
                        value={
                            'status': 'unhealthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'version': '1.0.0',
                            'services': {
                                'database': {
                                    'status': 'healthy',
                                    'response_time_ms': 2.5,
                                },
                                'redis': {
                                    'status': 'unhealthy',
                                    'error': 'Connection refused',
                                    'response_time_ms': None,
                                },
                            },
                        },
                    ),
                ],
            },
        },
    )
    def get(self, request):
        """
        Perform comprehensive health check.
        
        Returns:
            Response: JSON response with health status of all services
        """
        start_time = time.time()
    health_status = {
        'status': 'healthy',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime()),
            'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'services': {}
    }
    
        overall_healthy = True
        
        # Check database
        db_status = self._check_database()
        health_status['services']['database'] = db_status
        if db_status['status'] != 'healthy':
            overall_healthy = False
        
        # Check Redis
        redis_status = self._check_redis()
        health_status['services']['redis'] = redis_status
        # Redis is optional in development, but required in production
        if redis_status['status'] != 'healthy' and not settings.DEBUG:
            overall_healthy = False
        
        health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
        health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Log health check result
        if not overall_healthy:
            logger.warning(
                'Health check failed',
                extra={
                    'health_status': health_status,
                    'status_code': status_code,
                }
            )
        
        return Response(health_status, status=status_code)
    
    def _check_database(self):
        """
        Check database connectivity and response time.
        
        Returns:
            dict: Database health status with response time
        """
        start_time = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
            }
    except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            logger.error(
                'Database health check failed',
                exc_info=True,
                extra={
                    'error': str(e),
                    'response_time_ms': response_time,
                }
            )
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': response_time,
            }
    
    def _check_redis(self):
        """
        Check Redis connectivity and response time.
        
        Returns:
            dict: Redis health status with response time
        """
        start_time = time.time()
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
            if not redis_url:
                return {
                    'status': 'not_configured',
                    'message': 'Redis URL not configured',
                    'response_time_ms': None,
                }
            
            redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
            redis_client.ping()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
            }
        except redis.ConnectionError as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            logger.error(
                'Redis health check failed: Connection error',
                exc_info=True,
                extra={
                    'error': str(e),
                    'response_time_ms': response_time,
                }
            )
            return {
                'status': 'unhealthy',
                'error': f'Connection error: {str(e)}',
                'response_time_ms': response_time,
            }
        except redis.TimeoutError as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            logger.error(
                'Redis health check failed: Timeout',
                exc_info=True,
                extra={
                    'error': str(e),
                    'response_time_ms': response_time,
                }
            )
            return {
                'status': 'unhealthy',
                'error': f'Timeout: {str(e)}',
                'response_time_ms': response_time,
            }
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            logger.error(
                'Redis health check failed: Unexpected error',
                exc_info=True,
                extra={
                    'error': str(e),
                    'response_time_ms': response_time,
                }
            )
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time_ms': response_time,
            }


class DatabaseHealthCheckView(APIView):
    """
    Database-specific health check endpoint.
    
    Performs detailed database health checks including:
    - Connection verification
    - Query execution test
    - Response time measurement
    
    Useful for monitoring database performance and availability.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Health'],
        summary='Database health check',
        description="""
        Check the health status of the database connection.
        
        This endpoint performs:
        - Database connection verification
        - Simple query execution test
        - Response time measurement
        
        **Response Codes:**
        - `200 OK`: Database is healthy
        - `503 Service Unavailable`: Database is unhealthy
        
        **Use Cases:**
        - Database monitoring
        - Performance monitoring
        - Troubleshooting database issues
        - Load balancer database health checks
        
        **Note:** This endpoint does not require authentication.
        """,
        responses={
            200: {
                'description': 'Database is healthy',
                'examples': [
                    OpenApiExample(
                        'Healthy Database',
                        value={
                            'status': 'healthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'database': {
                                'engine': 'mysql',
                                'name': 'taskmanager',
                                'host': 'db',
                                'port': 3306,
                                'response_time_ms': 2.5,
                            },
                        },
                    ),
                ],
            },
            503: {
                'description': 'Database is unhealthy',
                'examples': [
                    OpenApiExample(
                        'Unhealthy Database',
                        value={
                            'status': 'unhealthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'database': {
                                'engine': 'mysql',
                                'name': 'taskmanager',
                                'host': 'db',
                                'port': 3306,
                                'error': 'Connection refused',
                                'response_time_ms': None,
                            },
                        },
                    ),
                ],
            },
        },
    )
    def get(self, request):
        """
        Perform database health check.
        
        Returns:
            Response: JSON response with database health status
        """
        start_time = time.time()
        db_config = settings.DATABASES['default']
        
        health_status = {
            'status': 'healthy',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime()),
            'database': {
                'engine': db_config.get('ENGINE', '').split('.')[-1],
                'name': db_config.get('NAME', ''),
                'host': db_config.get('HOST', ''),
                'port': db_config.get('PORT', ''),
            }
        }
        
        # Perform database check
        db_check_start = time.time()
        try:
            with connection.cursor() as cursor:
                # Test basic query
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                # Test database name
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]
                
                # Test connection info
                cursor.execute("SELECT CONNECTION_ID()")
                connection_id = cursor.fetchone()[0]
            
            response_time = round((time.time() - db_check_start) * 1000, 2)
            health_status['database']['response_time_ms'] = response_time
            health_status['database']['connection_id'] = connection_id
            health_status['database']['actual_database'] = db_name
            
            status_code = status.HTTP_200_OK
            
    except Exception as e:
            response_time = round((time.time() - db_check_start) * 1000, 2)
            health_status['status'] = 'unhealthy'
            health_status['database']['error'] = str(e)
            health_status['database']['response_time_ms'] = response_time
            health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                'Database health check failed',
                exc_info=True,
                extra={
                    'database_config': health_status['database'],
                    'error': str(e),
                }
            )
            
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        return Response(health_status, status=status_code)


class RedisHealthCheckView(APIView):
    """
    Redis-specific health check endpoint.
    
    Performs detailed Redis health checks including:
    - Connection verification
    - Ping test
    - Response time measurement
    - Basic Redis info retrieval
    
    Useful for monitoring Redis performance and availability.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Health'],
        summary='Redis health check',
        description="""
        Check the health status of the Redis connection.
        
        This endpoint performs:
        - Redis connection verification
        - Ping test
        - Response time measurement
        - Basic Redis server info
        
        **Response Codes:**
        - `200 OK`: Redis is healthy
        - `503 Service Unavailable`: Redis is unhealthy
        - `503 Service Unavailable`: Redis is not configured
        
        **Use Cases:**
        - Redis monitoring
        - Celery broker monitoring
        - Performance monitoring
        - Troubleshooting Redis issues
        
        **Note:** This endpoint does not require authentication.
        """,
        responses={
            200: {
                'description': 'Redis is healthy',
                'examples': [
                    OpenApiExample(
                        'Healthy Redis',
                        value={
                            'status': 'healthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'redis': {
                                'url': 'redis://redis:6379/0',
                                'response_time_ms': 1.2,
                                'server_info': {
                                    'redis_version': '7.0.0',
                                    'connected_clients': 5,
                                },
                            },
                        },
                    ),
                ],
            },
            503: {
                'description': 'Redis is unhealthy or not configured',
                'examples': [
                    OpenApiExample(
                        'Unhealthy Redis',
                        value={
                            'status': 'unhealthy',
                            'timestamp': '2024-01-15T10:30:45.123456Z',
                            'redis': {
                                'url': 'redis://redis:6379/0',
                                'error': 'Connection refused',
                                'response_time_ms': None,
                            },
                        },
                    ),
                ],
            },
        },
    )
    def get(self, request):
        """
        Perform Redis health check.
        
        Returns:
            Response: JSON response with Redis health status
        """
        start_time = time.time()
        redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
        
        health_status = {
            'status': 'healthy',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime()),
            'redis': {
                'url': redis_url or 'not_configured',
            }
        }
        
        if not redis_url:
            health_status['status'] = 'not_configured'
            health_status['redis']['error'] = 'Redis URL not configured'
            health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Perform Redis check
        redis_check_start = time.time()
        try:
            redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
            
            # Ping test
            ping_result = redis_client.ping()
            if not ping_result:
                raise Exception('Ping failed')
            
            # Get basic server info
            try:
                info = redis_client.info('server')
                health_status['redis']['server_info'] = {
                    'redis_version': info.get('redis_version', 'unknown'),
                    'connected_clients': info.get('connected_clients', 0),
                }
            except Exception:
                # If info command fails, continue without server info
                pass
            
            response_time = round((time.time() - redis_check_start) * 1000, 2)
            health_status['redis']['response_time_ms'] = response_time
            status_code = status.HTTP_200_OK
            
        except redis.ConnectionError as e:
            response_time = round((time.time() - redis_check_start) * 1000, 2)
            health_status['status'] = 'unhealthy'
            health_status['redis']['error'] = f'Connection error: {str(e)}'
            health_status['redis']['response_time_ms'] = response_time
            health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                'Redis health check failed: Connection error',
                exc_info=True,
                extra={
                    'redis_url': redis_url,
                    'error': str(e),
                }
            )
            
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            
        except redis.TimeoutError as e:
            response_time = round((time.time() - redis_check_start) * 1000, 2)
            health_status['status'] = 'unhealthy'
            health_status['redis']['error'] = f'Timeout: {str(e)}'
            health_status['redis']['response_time_ms'] = response_time
            health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                'Redis health check failed: Timeout',
                exc_info=True,
                extra={
                    'redis_url': redis_url,
                    'error': str(e),
                }
            )
            
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            
        except Exception as e:
            response_time = round((time.time() - redis_check_start) * 1000, 2)
            health_status['status'] = 'unhealthy'
            health_status['redis']['error'] = str(e)
            health_status['redis']['response_time_ms'] = response_time
            health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
            
            logger.error(
                'Redis health check failed: Unexpected error',
                exc_info=True,
                extra={
                    'redis_url': redis_url,
                    'error': str(e),
                }
            )
            
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        health_status['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        return Response(health_status, status=status_code)


# Backward compatibility: Keep the function-based view for simple use cases
def health_check(request):
    """
    Simple function-based health check endpoint (backward compatibility).
    
    This is a simple wrapper around HealthCheckView for backward compatibility.
    For new code, use HealthCheckView instead.
    """
    view = HealthCheckView()
    view.request = request
    return view.get(request)
