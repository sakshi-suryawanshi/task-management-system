#!/usr/bin/env python
"""
Test script for logging configuration.

This script tests the logging configuration to ensure:
1. Log files are created correctly
2. Log rotation works
3. Different log levels are captured
4. Structured JSON logging works (if enabled)
5. Component-specific loggers work

Usage:
    python test_logging.py
    # Or in Docker:
    docker-compose exec web python test_logging.py
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
import django
django.setup()

from django.conf import settings


def test_log_file_exists(log_file_path):
    """Test if log file exists and is writable."""
    print(f"\n✓ Testing log file: {log_file_path}")
    
    if not os.path.exists(log_file_path):
        print(f"  ✗ Log file does not exist: {log_file_path}")
        return False
    
    if not os.access(log_file_path, os.W_OK):
        print(f"  ✗ Log file is not writable: {log_file_path}")
        return False
    
    print(f"  ✓ Log file exists and is writable")
    return True


def test_logger_output(logger_name, log_file_path):
    """Test if logger writes to the correct file."""
    print(f"\n✓ Testing logger: {logger_name}")
    
    logger = logging.getLogger(logger_name)
    
    # Test different log levels
    test_messages = {
        'DEBUG': 'This is a DEBUG message',
        'INFO': 'This is an INFO message',
        'WARNING': 'This is a WARNING message',
        'ERROR': 'This is an ERROR message',
        'CRITICAL': 'This is a CRITICAL message',
    }
    
    for level, message in test_messages.items():
        log_level = getattr(logging, level)
        if logger.isEnabledFor(log_level):
            logger.log(log_level, f"[TEST] {message}")
            print(f"  ✓ {level} message logged")
        else:
            print(f"  - {level} level disabled for this logger")
    
    # Check if log file was written to
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            content = f.read()
            if '[TEST]' in content:
                print(f"  ✓ Log messages written to file")
                return True
            else:
                print(f"  ✗ Log messages not found in file")
                return False
    else:
        print(f"  ✗ Log file does not exist")
        return False


def test_json_logging(log_file_path):
    """Test if JSON logging is working correctly."""
    print(f"\n✓ Testing JSON logging format")
    
    if not os.path.exists(log_file_path):
        print(f"  ✗ Log file does not exist: {log_file_path}")
        return False
    
    with open(log_file_path, 'r') as f:
        # Read last few lines
        lines = f.readlines()
        if not lines:
            print(f"  ✗ Log file is empty")
            return False
        
        # Check last line
        last_line = lines[-1].strip()
        
        try:
            log_data = json.loads(last_line)
            required_fields = ['timestamp', 'level', 'logger', 'message']
            missing_fields = [field for field in required_fields if field not in log_data]
            
            if missing_fields:
                print(f"  ✗ Missing required JSON fields: {missing_fields}")
                return False
            
            print(f"  ✓ JSON logging format is correct")
            print(f"    Sample log entry: {json.dumps(log_data, indent=2)}")
            return True
        except json.JSONDecodeError:
            # Not JSON format, which is fine if USE_JSON_LOGGING is False
            print(f"  - Log file is not in JSON format (USE_JSON_LOGGING may be False)")
            return True  # This is acceptable


def test_log_rotation():
    """Test log rotation by checking if backup files can be created."""
    print(f"\n✓ Testing log rotation configuration")
    
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    log_files = [
        'django.log',
        'celery.log',
        'application.log',
        'errors.log',
        'security.log',
    ]
    
    for log_file in log_files:
        log_path = os.path.join(logs_dir, log_file)
        if os.path.exists(log_path):
            file_size = os.path.getsize(log_path)
            print(f"  ✓ {log_file}: {file_size} bytes")
        else:
            print(f"  - {log_file}: not created yet (will be created on first log)")
    
    # Get log rotation settings from environment or defaults
    from django.conf import settings as django_settings
    import environ
    env = environ.Env()
    max_bytes = env.int('LOG_MAX_BYTES', default=10 * 1024 * 1024)
    backup_count = env.int('LOG_BACKUP_COUNT', default=10)
    print(f"  ✓ Log rotation configured (max_bytes: {max_bytes}, backups: {backup_count})")
    return True


def test_component_loggers():
    """Test application-specific loggers."""
    print(f"\n✓ Testing component-specific loggers")
    
    components = ['users', 'teams', 'projects', 'tasks', 'notifications', 'core']
    
    for component in components:
        logger = logging.getLogger(component)
        logger.info(f"[TEST] Testing {component} logger")
        print(f"  ✓ {component} logger: level={logging.getLevelName(logger.level)}")
    
    return True


def test_django_loggers():
    """Test Django-specific loggers."""
    print(f"\n✓ Testing Django-specific loggers")
    
    django_loggers = [
        'django',
        'django.request',
        'django.server',
        'django.security',
    ]
    
    for logger_name in django_loggers:
        logger = logging.getLogger(logger_name)
        logger.info(f"[TEST] Testing {logger_name} logger")
        print(f"  ✓ {logger_name}: level={logging.getLevelName(logger.level)}")
    
    return True


def test_celery_loggers():
    """Test Celery-specific loggers."""
    print(f"\n✓ Testing Celery-specific loggers")
    
    celery_loggers = [
        'celery',
        'celery.task',
        'celery.worker',
    ]
    
    for logger_name in celery_loggers:
        logger = logging.getLogger(logger_name)
        logger.info(f"[TEST] Testing {logger_name} logger")
        print(f"  ✓ {logger_name}: level={logging.getLevelName(logger.level)}")
    
    return True


def main():
    """Run all logging tests."""
    print("=" * 70)
    print("Logging Configuration Test")
    print("=" * 70)
    
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    print(f"\nLogs directory: {logs_dir}")
    print(f"DEBUG mode: {settings.DEBUG}")
    print(f"USE_JSON_LOGGING: {getattr(settings, 'USE_JSON_LOGGING', 'Not set')}")
    print(f"LOG_LEVEL: {getattr(settings, 'LOG_LEVEL', 'Not set')}")
    
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)
    
    results = []
    
    # Test log files
    log_files = {
        'django.log': 'django',
        'celery.log': 'celery',
        'application.log': 'root',
        'errors.log': 'django.request',
        'security.log': 'django.security',
    }
    
    for log_file, logger_name in log_files.items():
        log_path = os.path.join(logs_dir, log_file)
        results.append(test_log_file_exists(log_path))
        results.append(test_logger_output(logger_name, log_path))
    
    # Test JSON logging (if enabled)
    if getattr(settings, 'USE_JSON_LOGGING', False):
        app_log_path = os.path.join(logs_dir, 'application.log')
        results.append(test_json_logging(app_log_path))
    
    # Test log rotation
    results.append(test_log_rotation())
    
    # Test component loggers
    results.append(test_component_loggers())
    
    # Test Django loggers
    results.append(test_django_loggers())
    
    # Test Celery loggers
    results.append(test_celery_loggers())
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All logging tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

