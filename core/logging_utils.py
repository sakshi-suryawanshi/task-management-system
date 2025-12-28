"""
Logging utilities for Task Management System.

This module provides helper functions for structured logging with context.
Use these utilities to add extra context (user, request, etc.) to log messages.
"""

import logging
from functools import wraps


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", extra={'user_id': user.id})
    """
    return logging.getLogger(name)


def log_with_context(logger, level, message, **context):
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **context: Additional context fields (user_id, request_id, etc.)
        
    Example:
        log_with_context(
            logger,
            logging.INFO,
            "Task created",
            user_id=user.id,
            task_id=task.id,
            project_id=task.project_id
        )
    """
    logger.log(level, message, extra=context)


def log_request(logger, request, message, level=logging.INFO, **extra_context):
    """
    Log a message with request context.
    
    Args:
        logger: Logger instance
        request: Django HttpRequest object
        message: Log message
        level: Log level (default: INFO)
        **extra_context: Additional context fields
        
    Example:
        log_request(
            logger,
            request,
            "API endpoint accessed",
            endpoint="/api/tasks/",
            method=request.method
        )
    """
    context = {
        'path': request.path,
        'method': request.method,
        'ip_address': get_client_ip(request),
        **extra_context
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        context['user_id'] = request.user.id
        context['username'] = request.user.username
    
    logger.log(level, message, extra=context)


def log_user_action(logger, user, action, level=logging.INFO, **extra_context):
    """
    Log a user action with user context.
    
    Args:
        logger: Logger instance
        user: User instance
        action: Action description
        level: Log level (default: INFO)
        **extra_context: Additional context fields
        
    Example:
        log_user_action(
            logger,
            user,
            "Task assigned",
            task_id=task.id,
            assignee_id=assignee.id
        )
    """
    context = {
        'user_id': user.id,
        'username': user.username,
        **extra_context
    }
    logger.log(level, action, extra=context)


def log_error_with_traceback(logger, message, exc_info=None, **context):
    """
    Log an error with full traceback.
    
    Args:
        logger: Logger instance
        message: Error message
        exc_info: Exception info (usually from sys.exc_info())
        **context: Additional context fields
        
    Example:
        try:
            # some code
        except Exception as e:
            log_error_with_traceback(
                logger,
                "Failed to process task",
                exc_info=sys.exc_info(),
                task_id=task.id
            )
    """
    logger.error(message, exc_info=exc_info, extra=context)


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_function_call(logger):
    """
    Decorator to log function calls with arguments and results.
    
    Args:
        logger: Logger instance
        
    Example:
        @log_function_call(logger)
        def create_task(title, description):
            # function implementation
            return task
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    'function': func.__name__,
                    'module': func.__module__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"{func.__name__} completed successfully",
                    extra={
                        'function': func.__name__,
                        'module': func.__module__
                    }
                )
                return result
            except Exception as e:
                logger.error(
                    f"{func.__name__} raised exception: {str(e)}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'module': func.__module__
                    }
                )
                raise
        return wrapper
    return decorator

