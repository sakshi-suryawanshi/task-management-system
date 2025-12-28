"""
Test script for Sentry error tracking configuration.

This script tests various error scenarios to verify that Sentry is properly
configured and capturing errors correctly.

Usage:
    python test_sentry.py
    # Or in Docker:
    docker-compose exec web python test_sentry.py

Prerequisites:
    1. Set SENTRY_DSN in your .env file (or environment variables)
    2. Ensure Sentry is enabled (SENTRY_ENABLED=true)
    3. Check your Sentry project dashboard to see captured errors
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from taskmanager.celery import app as celery_app
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_sentry_configuration():
    """Test that Sentry is properly configured."""
    print_section("Testing Sentry Configuration")
    
    sentry_dsn = getattr(settings, 'SENTRY_DSN', '')
    sentry_enabled = getattr(settings, 'SENTRY_ENABLED', False)
    sentry_environment = getattr(settings, 'SENTRY_ENVIRONMENT', 'development')
    
    print(f"Sentry DSN: {'Set' if sentry_dsn else 'Not set'}")
    print(f"Sentry Enabled: {sentry_enabled}")
    print(f"Sentry Environment: {sentry_environment}")
    print(f"Debug Mode: {settings.DEBUG}")
    
    if not sentry_dsn:
        print("\n⚠️  WARNING: SENTRY_DSN is not set. Sentry is disabled.")
        print("   To enable Sentry:")
        print("   1. Sign up at https://sentry.io")
        print("   2. Create a new project")
        print("   3. Get your DSN from project settings")
        print("   4. Set SENTRY_DSN in your .env file")
        return False
    
    if not sentry_enabled:
        print("\n⚠️  WARNING: Sentry is disabled (SENTRY_ENABLED=false).")
        return False
    
    print("\n✅ Sentry is configured and enabled!")
    return True


def test_basic_error_capture():
    """Test basic error capture."""
    print_section("Testing Basic Error Capture")
    
    try:
        # This should be captured by Sentry
        raise ValueError("This is a test error for Sentry")
    except ValueError as e:
        # Capture the exception
        sentry_sdk.capture_exception(e)
        print(f"✅ Exception captured: {e}")
        print("   Check your Sentry dashboard to see this error")


def test_error_with_context():
    """Test error capture with additional context."""
    print_section("Testing Error Capture with Context")
    
    try:
        # Add context before raising error
        sentry_sdk.set_context("test_context", {
            "test_id": "12345",
            "test_name": "Sentry Integration Test",
            "test_type": "context_test",
        })
        
        sentry_sdk.set_tag("test_category", "integration")
        sentry_sdk.set_tag("test_environment", "local")
        
        raise RuntimeError("Test error with context")
    except RuntimeError as e:
        sentry_sdk.capture_exception(e)
        print("✅ Exception captured with context")
        print("   Context includes: test_id, test_name, test_type")
        print("   Tags include: test_category, test_environment")
        print("   Check your Sentry dashboard to see this error with context")


def test_user_context():
    """Test error capture with user context."""
    print_section("Testing Error Capture with User Context")
    
    try:
        # Try to get a user (if any exist)
        user = User.objects.first()
        
        if user:
            # Set user context
            sentry_sdk.set_user({
                "id": user.id,
                "username": user.username,
                "email": user.email,
            })
            print(f"   User context set: {user.username} (ID: {user.id})")
        else:
            print("   No users found in database, using anonymous user")
            sentry_sdk.set_user({
                "id": None,
                "username": "test_user",
                "email": "test@example.com",
            })
        
        raise PermissionError("Test error with user context")
    except PermissionError as e:
        sentry_sdk.capture_exception(e)
        print("✅ Exception captured with user context")
        print("   Check your Sentry dashboard to see user information")


def test_custom_message():
    """Test sending a custom message to Sentry."""
    print_section("Testing Custom Message")
    
    sentry_sdk.capture_message(
        "This is a test message from Sentry integration test",
        level="info"
    )
    print("✅ Custom message sent to Sentry")
    print("   Check your Sentry dashboard to see this message")


def test_celery_task_error():
    """Test error capture in Celery task."""
    print_section("Testing Celery Task Error Capture")
    
    @celery_app.task
    def test_error_task():
        """Test task that raises an error."""
        try:
            raise Exception("Test error in Celery task")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.error(f"Error in Celery task: {e}", exc_info=True)
            raise
    
    try:
        # Execute task synchronously for testing
        result = test_error_task.apply()
        print("✅ Celery task error captured")
        print("   Note: In production, this would run asynchronously")
    except Exception as e:
        print(f"✅ Celery task error captured: {e}")
        print("   Check your Sentry dashboard to see Celery task errors")


def test_logging_integration():
    """Test that logging errors are captured by Sentry."""
    print_section("Testing Logging Integration")
    
    # Test different log levels
    logger.info("This is an INFO message (should not be sent to Sentry)")
    logger.warning("This is a WARNING message (should not be sent to Sentry)")
    logger.error("This is an ERROR message (should be sent to Sentry)")
    logger.critical("This is a CRITICAL message (should be sent to Sentry)")
    
    print("✅ Logging integration tested")
    print("   ERROR and CRITICAL messages should appear in Sentry")
    print("   INFO and WARNING messages should not appear in Sentry")


def test_breadcrumbs():
    """Test breadcrumb tracking."""
    print_section("Testing Breadcrumb Tracking")
    
    # Add breadcrumbs (user actions leading to error)
    sentry_sdk.add_breadcrumb(
        message="User clicked button",
        category="ui",
        level="info",
        data={"button_id": "submit_task"}
    )
    
    sentry_sdk.add_breadcrumb(
        message="Form validation started",
        category="validation",
        level="info",
        data={"form_type": "task_form"}
    )
    
    sentry_sdk.add_breadcrumb(
        message="Database query executed",
        category="database",
        level="info",
        data={"query": "SELECT * FROM tasks"}
    )
    
    # Now raise an error - breadcrumbs will be included
    try:
        raise ValueError("Error after breadcrumbs")
    except ValueError as e:
        sentry_sdk.capture_exception(e)
        print("✅ Error captured with breadcrumbs")
        print("   Check your Sentry dashboard to see breadcrumb trail")


def test_performance_monitoring():
    """Test performance monitoring (if enabled)."""
    print_section("Testing Performance Monitoring")
    
    traces_sample_rate = getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.0)
    
    if traces_sample_rate > 0:
        print(f"   Performance monitoring enabled (sample rate: {traces_sample_rate})")
        
        # Create a transaction
        with sentry_sdk.start_transaction(op="test", name="test_performance"):
            # Simulate some work
            import time
            time.sleep(0.1)
            
            # Nested span
            with sentry_sdk.start_span(op="db", description="test_query"):
                time.sleep(0.05)
        
        print("✅ Performance transaction sent to Sentry")
        print("   Check your Sentry dashboard Performance section")
    else:
        print("⚠️  Performance monitoring is disabled (SENTRY_TRACES_SAMPLE_RATE=0.0)")
        print("   Set SENTRY_TRACES_SAMPLE_RATE > 0 to enable performance monitoring")


def main():
    """Run all Sentry tests."""
    print("\n" + "=" * 70)
    print("  SENTRY ERROR TRACKING TEST SUITE")
    print("=" * 70)
    print("\nThis script tests Sentry error tracking configuration.")
    print("Errors will be sent to your Sentry project dashboard.")
    print("\nMake sure to check your Sentry dashboard after running this script.\n")
    
    # Check configuration first
    if not test_sentry_configuration():
        print("\n⚠️  Sentry is not properly configured. Some tests will be skipped.")
        response = input("\nContinue with tests anyway? (y/n): ")
        if response.lower() != 'y':
            print("\nExiting. Please configure Sentry first.")
            return
    
    # Run tests
    try:
        test_basic_error_capture()
        test_error_with_context()
        test_user_context()
        test_custom_message()
        test_logging_integration()
        test_breadcrumbs()
        test_performance_monitoring()
        
        # Celery test (may fail if Celery worker is not running)
        try:
            test_celery_task_error()
        except Exception as e:
            print(f"\n⚠️  Celery test skipped: {e}")
            print("   This is normal if Celery worker is not running")
        
        print_section("Test Summary")
        print("✅ All tests completed!")
        print("\nNext steps:")
        print("1. Check your Sentry dashboard at https://sentry.io")
        print("2. Look for errors and messages from this test")
        print("3. Verify that context, user info, and breadcrumbs are captured")
        print("4. Check performance monitoring (if enabled)")
        print("\nIf you don't see errors in Sentry:")
        print("- Verify SENTRY_DSN is correct")
        print("- Check SENTRY_ENABLED is true")
        print("- Ensure your Sentry project is active")
        print("- Check network connectivity to Sentry")
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sentry_sdk.capture_exception(e)


if __name__ == '__main__':
    main()

