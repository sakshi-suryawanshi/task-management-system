#!/usr/bin/env python
"""
Send a real email to sakshiss.dev@gmail.com using the email tasks.

This script sends a welcome email to the specified email address to test
that email sending works with real SMTP configuration.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from django.conf import settings
from users.models import User
from notifications.tasks import send_welcome_email

# Target email
TARGET_EMAIL = 'sakshiss.dev@gmail.com'

print("=" * 80)
print("  SENDING REAL EMAIL TEST")
print("=" * 80)
print()

# Check email configuration
print("Checking email configuration...")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'Not set'}")
print()

if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
    print("⚠️  WARNING: EMAIL_BACKEND is not SMTP!")
    print(f"   Current: {settings.EMAIL_BACKEND}")
    print("   Please set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend in .env")
    print()

if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("⚠️  WARNING: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not configured!")
    print("   Please set these in your .env file")
    print()
    print("   For Gmail, you need:")
    print("   EMAIL_HOST_USER=sakshiss.dev@gmail.com")
    print("   EMAIL_HOST_PASSWORD=your-app-password")
    print()
    print("   Note: You need to generate an App Password from Google:")
    print("   1. Go to https://myaccount.google.com/apppasswords")
    print("   2. Generate a new app password for 'Mail'")
    print("   3. Use that password (not your regular Gmail password)")
    print()
    sys.exit(1)

print("✅ Email configuration looks good!")
print()

# Get or create user with target email
print(f"Getting or creating user with email: {TARGET_EMAIL}")
try:
    user = User.objects.filter(email=TARGET_EMAIL).first()
    if not user:
        # Create user for testing
        user = User.objects.create_user(
            username='sakshiss_dev',
            email=TARGET_EMAIL,
            password='temp_password_123',  # Not important for email test
            first_name='Sakshi',
            last_name='Dev'
        )
        print(f"✅ Created test user: {user.email}")
    else:
        print(f"✅ Using existing user: {user.email}")
        # Update name for better email
        user.first_name = 'Sakshi'
        user.last_name = 'Dev'
        user.save()
        print(f"✅ Updated user name")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Ensure profile exists with email notifications enabled
try:
    profile = user.profile
    profile.email_notifications = True
    profile.save()
except:
    from users.models import UserProfile
    UserProfile.objects.create(user=user, email_notifications=True)

print()

# Send welcome email
print("=" * 80)
print(f"Sending welcome email to {TARGET_EMAIL}...")
print("=" * 80)
print()

try:
    result = send_welcome_email(user.id)
    
    print(f"Task Result: {result}")
    print()
    
    if result.get('status') == 'success':
        print("✅ SUCCESS!")
        print(f"✅ Email sent successfully to {TARGET_EMAIL}")
        print()
        print("Please check your inbox (and spam folder) for the welcome email.")
        print("The email should have:")
        print("  - Professional HTML formatting")
        print("  - Welcome message")
        print("  - Getting started guide")
        print("  - Links to login and dashboard")
    elif result.get('status') == 'skipped':
        print(f"⚠️  Email was skipped: {result.get('reason')}")
    else:
        print(f"❌ Error: {result.get('error')}")
        
except Exception as e:
    print(f"❌ ERROR sending email: {e}")
    print()
    print("Common issues:")
    print("1. Gmail App Password not set correctly")
    print("2. 2FA not enabled on Gmail account")
    print("3. 'Less secure app access' needs to be enabled (or use App Password)")
    print("4. Network/firewall blocking SMTP connection")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

