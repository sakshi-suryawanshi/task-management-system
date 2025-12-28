#!/bin/bash

# Manual Test Script for Task 3.3: User Profile Management
# This script tests all profile endpoints using curl

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo ""
}

# Check if server is running
print_header "Checking Server Connection"
if curl -s -f "${BASE_URL}/health/" > /dev/null 2>&1; then
    print_success "Server is running"
else
    print_error "Server is not running. Please start Docker services: docker-compose up -d"
    exit 1
fi

# Test 1: User Registration
print_header "TEST 1: User Registration"
TIMESTAMP=$(date +%s)
USERNAME="testuser_${TIMESTAMP}"
EMAIL="test_${TIMESTAMP}@example.com"

REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"email\": \"${EMAIL}\",
    \"password\": \"TestPass123!\",
    \"password2\": \"TestPass123!\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\",
    \"role\": \"developer\",
    \"phone\": \"+1234567890\",
    \"bio\": \"Test user for profile testing\"
  }")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    print_success "User registered successfully: ${USERNAME}"
    ACCESS_TOKEN=$(echo "$BODY" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "Could not extract access token from registration response"
        exit 1
    fi
    print_info "Access token received: ${ACCESS_TOKEN:0:50}..."
else
    print_error "Registration failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi

# Test 2: User Login (alternative method)
print_header "TEST 2: User Login"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"${USERNAME}\",
    \"password\": \"TestPass123!\"
  }")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Login successful"
    ACCESS_TOKEN=$(echo "$BODY" | grep -o '"access":"[^"]*' | cut -d'"' -f4)
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "Could not extract access token from login response"
        exit 1
    fi
    print_info "Access token: ${ACCESS_TOKEN:0:50}..."
else
    print_error "Login failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi

# Test 3: GET Profile
print_header "TEST 3: GET Profile"
GET_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$GET_RESPONSE" | tail -n1)
BODY=$(echo "$GET_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Profile retrieved successfully"
    USERNAME_FROM_PROFILE=$(echo "$BODY" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
    EMAIL_FROM_PROFILE=$(echo "$BODY" | grep -o '"email":"[^"]*' | cut -d'"' -f4)
    FULL_NAME=$(echo "$BODY" | grep -o '"full_name":"[^"]*' | cut -d'"' -f4)
    print_info "Username: ${USERNAME_FROM_PROFILE}"
    print_info "Email: ${EMAIL_FROM_PROFILE}"
    print_info "Full Name: ${FULL_NAME}"
else
    print_error "GET profile failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
fi

# Test 4: PUT Profile (Full Update)
print_header "TEST 4: PUT Profile (Full Update)"
PUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
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
    "email_notifications": true,
    "push_notifications": true
  }')

HTTP_CODE=$(echo "$PUT_RESPONSE" | tail -n1)
BODY=$(echo "$PUT_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Profile updated successfully via PUT"
    MESSAGE=$(echo "$BODY" | grep -o '"message":"[^"]*' | cut -d'"' -f4)
    print_info "Message: ${MESSAGE}"
    BIO=$(echo "$BODY" | grep -o '"bio":"[^"]*' | cut -d'"' -f4)
    JOB_TITLE=$(echo "$BODY" | grep -o '"job_title":"[^"]*' | cut -d'"' -f4)
    print_info "Updated Bio: ${BIO}"
    print_info "Updated Job Title: ${JOB_TITLE}"
else
    print_error "PUT profile failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
fi

# Test 5: PATCH Profile (Partial Update)
print_header "TEST 5: PATCH Profile (Partial Update)"
PATCH_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Updated bio via PATCH request - Partial update test",
    "job_title": "Lead Developer",
    "city": "New York",
    "email_notifications": false
  }')

HTTP_CODE=$(echo "$PATCH_RESPONSE" | tail -n1)
BODY=$(echo "$PATCH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Profile updated successfully via PATCH"
    BIO=$(echo "$BODY" | grep -o '"bio":"[^"]*' | cut -d'"' -f4)
    JOB_TITLE=$(echo "$BODY" | grep -o '"job_title":"[^"]*' | cut -d'"' -f4)
    CITY=$(echo "$BODY" | grep -o '"city":"[^"]*' | cut -d'"' -f4)
    print_info "Updated Bio: ${BIO}"
    print_info "Updated Job Title: ${JOB_TITLE}"
    print_info "Updated City: ${CITY}"
else
    print_error "PATCH profile failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
fi

# Test 6: Unauthorized Access
print_header "TEST 6: Unauthorized Access Test"
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}/api/auth/profile/" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n1)
BODY=$(echo "$UNAUTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 401 ]; then
    print_success "Unauthorized access correctly rejected (401)"
else
    print_error "Expected 401, got $HTTP_CODE"
fi

# Test 7: Validation Errors
print_header "TEST 7: Validation Error Tests"

# Test invalid role
print_info "Testing invalid role..."
INVALID_ROLE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role": "invalid_role"}')

HTTP_CODE=$(echo "$INVALID_ROLE_RESPONSE" | tail -n1)
BODY=$(echo "$INVALID_ROLE_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 400 ]; then
    print_success "Invalid role correctly rejected"
else
    print_error "Expected 400 for invalid role, got $HTTP_CODE"
fi

# Test invalid LinkedIn URL
print_info "Testing invalid LinkedIn URL..."
INVALID_LINKEDIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"linkedin": "https://invalid-url.com"}')

HTTP_CODE=$(echo "$INVALID_LINKEDIN_RESPONSE" | tail -n1)
BODY=$(echo "$INVALID_LINKEDIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 400 ]; then
    print_success "Invalid LinkedIn URL correctly rejected"
else
    print_error "Expected 400 for invalid LinkedIn URL, got $HTTP_CODE"
fi

# Test 8: Verify Database Persistence
print_header "TEST 8: Database Persistence Verification"
TEST_BIO="Persistence test $(date +%s)"

# Update profile
UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "${BASE_URL}/api/auth/profile/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"bio\": \"${TEST_BIO}\"}")

HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -eq 200 ]; then
    # Wait a moment
    sleep 1
    
    # Retrieve profile again
    GET_RESPONSE2=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}/api/auth/profile/" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json")
    
    HTTP_CODE2=$(echo "$GET_RESPONSE2" | tail -n1)
    BODY2=$(echo "$GET_RESPONSE2" | sed '$d')
    
    if [ "$HTTP_CODE2" -eq 200 ]; then
        RETRIEVED_BIO=$(echo "$BODY2" | grep -o '"bio":"[^"]*' | cut -d'"' -f4)
        if [ "$RETRIEVED_BIO" = "$TEST_BIO" ]; then
            print_success "Database persistence verified"
            print_info "Bio value persisted correctly"
        else
            print_error "Bio not persisted correctly"
            print_info "Expected: ${TEST_BIO}"
            print_info "Got: ${RETRIEVED_BIO}"
        fi
    else
        print_error "Failed to retrieve profile for persistence check"
    fi
else
    print_error "Failed to update profile for persistence test"
fi

# Summary
print_header "TEST SUMMARY"
TOTAL=$((PASSED + FAILED))
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
else
    echo -e "${GREEN}All tests passed!${NC}"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Task 3.3 is working correctly!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the errors above.${NC}"
    exit 1
fi

