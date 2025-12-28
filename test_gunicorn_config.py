#!/usr/bin/env python
"""
Test script to validate gunicorn_config.py configuration.

This script checks that:
1. The config file can be imported without errors
2. Required configuration variables are set
3. Configuration values are valid

Usage:
    python test_gunicorn_config.py
"""

import os
import sys
import importlib.util

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_config_import():
    """Test that gunicorn_config.py can be imported."""
    print_info("Testing gunicorn_config.py import...")
    
    try:
        spec = importlib.util.spec_from_file_location(
            "gunicorn_config",
            os.path.join(os.path.dirname(__file__), "gunicorn_config.py")
        )
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        print_success("Config file imported successfully")
        return config
    except Exception as e:
        print_error(f"Failed to import config file: {e}")
        return None

def test_required_variables(config):
    """Test that required configuration variables are set."""
    print_info("Testing required configuration variables...")
    
    required_vars = [
        'bind',
        'workers',
        'worker_class',
        'timeout',
        'accesslog',
        'errorlog',
        'loglevel',
    ]
    
    missing = []
    for var in required_vars:
        if not hasattr(config, var):
            missing.append(var)
    
    if missing:
        print_error(f"Missing required variables: {', '.join(missing)}")
        return False
    
    print_success("All required variables are present")
    return True

def test_config_values(config):
    """Test that configuration values are valid."""
    print_info("Testing configuration values...")
    
    issues = []
    
    # Test bind address
    if not config.bind or not isinstance(config.bind, str):
        issues.append("bind must be a non-empty string")
    
    # Test workers
    if not isinstance(config.workers, int) or config.workers < 1:
        issues.append("workers must be a positive integer")
    
    # Test timeout
    if not isinstance(config.timeout, int) or config.timeout < 1:
        issues.append("timeout must be a positive integer")
    
    # Test loglevel
    valid_log_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if config.loglevel.lower() not in valid_log_levels:
        issues.append(f"loglevel must be one of: {', '.join(valid_log_levels)}")
    
    # Test worker_class
    if not config.worker_class or not isinstance(config.worker_class, str):
        issues.append("worker_class must be a non-empty string")
    
    if issues:
        for issue in issues:
            print_error(issue)
        return False
    
    print_success("All configuration values are valid")
    return True

def display_config_summary(config):
    """Display a summary of the configuration."""
    print_info("\nConfiguration Summary:")
    print(f"  Bind address: {config.bind}")
    print(f"  Workers: {config.workers}")
    print(f"  Worker class: {config.worker_class}")
    print(f"  Threads: {config.threads}")
    print(f"  Timeout: {config.timeout}s")
    print(f"  Graceful timeout: {config.graceful_timeout}s")
    print(f"  Max requests: {config.max_requests}")
    print(f"  Log level: {config.loglevel}")
    print(f"  Access log: {config.accesslog}")
    print(f"  Error log: {config.errorlog}")

def main():
    """Main test function."""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("Gunicorn Configuration Test")
    print("=" * 60)
    print(Colors.RESET)
    
    # Test 1: Import config
    config = test_config_import()
    if not config:
        print_error("Config import failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Test 2: Required variables
    if not test_required_variables(config):
        print_error("Required variables check failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Test 3: Config values
    if not test_config_values(config):
        print_error("Configuration values check failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Display summary
    display_config_summary(config)
    
    print()
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print(Colors.RESET)
    print()
    print_info("Next steps:")
    print("  1. Start Docker services: docker-compose up -d")
    print("  2. Check logs: docker-compose logs web")
    print("  3. Test health endpoint: curl http://localhost:8000/health/")
    print()

if __name__ == '__main__':
    main()

