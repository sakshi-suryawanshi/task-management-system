#!/usr/bin/env python3
"""
Manual test script for Task 3.3: User Profile Management

This script tests all profile endpoints:
- GET /api/auth/profile/
- PUT /api/auth/profile/
- PATCH /api/auth/profile/

Run this script to verify all functionality works correctly.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Colors for output
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

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_registration():
    """Test user registration"""
    print_header("TEST 1: User Registration")
    
    # Generate unique username
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@example.com"
    
    registration_data = {
        "username": username,
        "email": email,
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "developer",
        "phone": "+1234567890",
        "bio": "Test user for profile testing"
    }
    
    print_info(f"Registering user: {username}")
    response = requests.post(
        f"{BASE_URL}/api/auth/register/",
        json=registration_data
    )
    
    if response.status_code == 201:
        data = response.json()
        print_success(f"User registered successfully: {username}")
        print_info(f"User ID: {data['user']['id']}")
        return {
            'username': username,
            'email': email,
            'password': "TestPass123!",
            'user_id': data['user']['id'],
            'tokens': data['tokens']
        }
    else:
        print_error(f"Registration failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def test_login(username, password):
    """Test user login"""
    print_header("TEST 2: User Login")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    print_info(f"Logging in as: {username}")
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json=login_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Login successful")
        print_info(f"Access token received: {data['tokens']['access'][:50]}...")
        return data['tokens']
    else:
        print_error(f"Login failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def test_get_profile(access_token):
    """Test GET profile endpoint"""
    print_header("TEST 3: GET Profile")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print_info("Fetching user profile...")
    response = requests.get(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Profile retrieved successfully")
        print_info(f"Username: {data.get('username')}")
        print_info(f"Email: {data.get('email')}")
        print_info(f"Full Name: {data.get('full_name')}")
        print_info(f"Role: {data.get('role')}")
        print_info(f"Bio: {data.get('bio', 'N/A')}")
        print_info(f"Job Title: {data.get('job_title', 'N/A')}")
        print_info(f"Department: {data.get('department', 'N/A')}")
        return data
    else:
        print_error(f"Get profile failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def test_put_profile(access_token):
    """Test PUT profile endpoint (full update)"""
    print_header("TEST 4: PUT Profile (Full Update)")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "role": "developer",
        "bio": "Updated bio via PUT request - Full profile update test",
        "phone": "+1987654321",
        "job_title": "Senior Software Developer",
        "department": "Engineering",
        "location": "remote",
        "address": "123 Main Street",
        "city": "San Francisco",
        "country": "USA",
        "website": "https://johndoe.dev",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
        "twitter": "https://twitter.com/johndoe",
        "timezone": "America/Los_Angeles",
        "language": "en",
        "email_notifications": True,
        "push_notifications": True
    }
    
    print_info("Updating profile with PUT (full update)...")
    print_info(f"Updating {len(update_data)} fields")
    
    response = requests.put(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Profile updated successfully via PUT")
        print_info(f"Message: {data.get('message')}")
        print_info(f"Updated Bio: {data['data'].get('bio')}")
        print_info(f"Updated Job Title: {data['data'].get('job_title')}")
        print_info(f"Updated City: {data['data'].get('city')}")
        return data['data']
    else:
        print_error(f"PUT profile failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def test_patch_profile(access_token):
    """Test PATCH profile endpoint (partial update)"""
    print_header("TEST 5: PATCH Profile (Partial Update)")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Only update a few fields
    update_data = {
        "bio": "Updated bio via PATCH request - Partial update test",
        "job_title": "Lead Developer",
        "city": "New York",
        "email_notifications": False
    }
    
    print_info("Updating profile with PATCH (partial update)...")
    print_info(f"Updating only {len(update_data)} fields")
    
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success("Profile updated successfully via PATCH")
        print_info(f"Message: {data.get('message')}")
        print_info(f"Updated Bio: {data['data'].get('bio')}")
        print_info(f"Updated Job Title: {data['data'].get('job_title')}")
        print_info(f"Updated City: {data['data'].get('city')}")
        print_info(f"Email Notifications: {data['data'].get('email_notifications')}")
        # Verify other fields are unchanged
        print_info(f"Department (unchanged): {data['data'].get('department')}")
        print_info(f"Country (unchanged): {data['data'].get('country')}")
        return data['data']
    else:
        print_error(f"PATCH profile failed: {response.status_code}")
        print_error(f"Response: {response.text}")
        return None

def test_unauthorized_access():
    """Test unauthorized access (no token)"""
    print_header("TEST 6: Unauthorized Access Test")
    
    print_info("Attempting to access profile without token...")
    response = requests.get(
        f"{BASE_URL}/api/auth/profile/",
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 401:
        print_success("Unauthorized access correctly rejected (401)")
        print_info(f"Response: {response.json().get('detail', 'N/A')}")
        return True
    else:
        print_error(f"Expected 401, got {response.status_code}")
        return False

def test_validation_errors(access_token):
    """Test validation errors"""
    print_header("TEST 7: Validation Error Tests")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test invalid role
    print_info("Testing invalid role...")
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json={"role": "invalid_role"}
    )
    
    if response.status_code == 400:
        print_success("Invalid role correctly rejected")
        errors = response.json()
        print_info(f"Error: {errors.get('role', 'N/A')}")
    else:
        print_error(f"Expected 400 for invalid role, got {response.status_code}")
    
    # Test invalid LinkedIn URL
    print_info("\nTesting invalid LinkedIn URL...")
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json={"linkedin": "https://invalid-url.com"}
    )
    
    if response.status_code == 400:
        print_success("Invalid LinkedIn URL correctly rejected")
        errors = response.json()
        print_info(f"Error: {errors.get('linkedin', 'N/A')}")
    else:
        print_error(f"Expected 400 for invalid LinkedIn URL, got {response.status_code}")
    
    # Test invalid GitHub URL
    print_info("\nTesting invalid GitHub URL...")
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json={"github": "https://invalid-url.com"}
    )
    
    if response.status_code == 400:
        print_success("Invalid GitHub URL correctly rejected")
        errors = response.json()
        print_info(f"Error: {errors.get('github', 'N/A')}")
    else:
        print_error(f"Expected 400 for invalid GitHub URL, got {response.status_code}")
    
    return True

def test_readonly_fields(access_token):
    """Test that readonly fields cannot be updated"""
    print_header("TEST 8: Readonly Fields Test")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Try to update readonly fields
    update_data = {
        "username": "newusername",
        "email": "newemail@example.com",
        "id": 999
    }
    
    print_info("Attempting to update readonly fields (username, email, id)...")
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        # Check if readonly fields were actually changed
        if data.get('username') == update_data['username']:
            print_error("Readonly field 'username' was updated (should not be)")
            return False
        elif data.get('email') == update_data['email']:
            print_error("Readonly field 'email' was updated (should not be)")
            return False
        else:
            print_success("Readonly fields correctly ignored")
            print_info(f"Username unchanged: {data.get('username')}")
            print_info(f"Email unchanged: {data.get('email')}")
            return True
    else:
        print_error(f"Unexpected status code: {response.status_code}")
        return False

def verify_database_persistence(access_token):
    """Verify that changes are persisted in database"""
    print_header("TEST 9: Database Persistence Verification")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Make an update
    test_value = f"Persistence test {datetime.now().isoformat()}"
    update_data = {"bio": test_value}
    
    print_info("Making a profile update...")
    response = requests.patch(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers,
        json=update_data
    )
    
    if response.status_code != 200:
        print_error("Failed to update profile")
        return False
    
    # Wait a moment
    import time
    time.sleep(1)
    
    # Retrieve profile again
    print_info("Retrieving profile to verify persistence...")
    response = requests.get(
        f"{BASE_URL}/api/auth/profile/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('bio') == test_value:
            print_success("Database persistence verified")
            print_info(f"Bio value persisted: {data.get('bio')}")
            return True
        else:
            print_error(f"Bio not persisted correctly. Expected: {test_value}, Got: {data.get('bio')}")
            return False
    else:
        print_error("Failed to retrieve profile")
        return False

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("  TASK 3.3: USER PROFILE MANAGEMENT - MANUAL TESTING")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    try:
        # Test 1: Registration
        user_data = test_registration()
        if user_data:
            results['passed'] += 1
            results['tests'].append(('Registration', True))
        else:
            results['failed'] += 1
            results['tests'].append(('Registration', False))
            print_error("Cannot continue without registered user")
            return
        
        # Test 2: Login
        tokens = test_login(user_data['username'], user_data['password'])
        if tokens:
            results['passed'] += 1
            results['tests'].append(('Login', True))
            access_token = tokens['access']
        else:
            results['failed'] += 1
            results['tests'].append(('Login', False))
            print_error("Cannot continue without access token")
            return
        
        # Test 3: GET Profile
        profile = test_get_profile(access_token)
        if profile:
            results['passed'] += 1
            results['tests'].append(('GET Profile', True))
        else:
            results['failed'] += 1
            results['tests'].append(('GET Profile', False))
        
        # Test 4: PUT Profile
        updated_profile = test_put_profile(access_token)
        if updated_profile:
            results['passed'] += 1
            results['tests'].append(('PUT Profile', True))
        else:
            results['failed'] += 1
            results['tests'].append(('PUT Profile', False))
        
        # Test 5: PATCH Profile
        patched_profile = test_patch_profile(access_token)
        if patched_profile:
            results['passed'] += 1
            results['tests'].append(('PATCH Profile', True))
        else:
            results['failed'] += 1
            results['tests'].append(('PATCH Profile', False))
        
        # Test 6: Unauthorized Access
        if test_unauthorized_access():
            results['passed'] += 1
            results['tests'].append(('Unauthorized Access', True))
        else:
            results['failed'] += 1
            results['tests'].append(('Unauthorized Access', False))
        
        # Test 7: Validation Errors
        if test_validation_errors(access_token):
            results['passed'] += 1
            results['tests'].append(('Validation Errors', True))
        else:
            results['failed'] += 1
            results['tests'].append(('Validation Errors', False))
        
        # Test 8: Readonly Fields
        if test_readonly_fields(access_token):
            results['passed'] += 1
            results['tests'].append(('Readonly Fields', True))
        else:
            results['failed'] += 1
            results['tests'].append(('Readonly Fields', False))
        
        # Test 9: Database Persistence
        if verify_database_persistence(access_token):
            results['passed'] += 1
            results['tests'].append(('Database Persistence', True))
        else:
            results['failed'] += 1
            results['tests'].append(('Database Persistence', False))
        
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Make sure Docker services are running.")
        print_info("Run: docker-compose up -d")
        return
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    else:
        print_success("All tests passed!")
    
    print("\nDetailed Results:")
    for test_name, passed in results['tests']:
        if passed:
            print_success(f"  {test_name}")
        else:
            print_error(f"  {test_name}")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    if results['failed'] == 0:
        print_success("🎉 ALL TESTS PASSED! Task 3.3 is working correctly!")
        return 0
    else:
        print_error("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

