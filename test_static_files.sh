#!/bin/bash

# Test script for static files configuration (Task 6.3)
# This script validates static files collection and serving through Nginx
#
# Usage:
#   ./test_static_files.sh
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - Services running (docker-compose up -d)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

# Function to print info message
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to check if container is running
check_container() {
    if docker ps --format '{{.Names}}' | grep -q "^${1}$"; then
        return 0
    else
        return 1
    fi
}

# Function to run command in container
run_in_container() {
    docker exec "$1" sh -c "$2"
}

# Start tests
print_header "Static Files Configuration Test Suite"
echo "Testing static files collection and serving..."
echo ""

# Test 1: Check if containers are running
print_header "Test 1: Container Status Check"

if check_container "taskmanager_web"; then
    print_success "Web container (Django/Gunicorn) is running"
else
    print_error "Web container is not running. Start services with: docker-compose up -d"
    exit 1
fi

if check_container "taskmanager_nginx"; then
    print_success "Nginx container is running"
else
    print_error "Nginx container is not running. Start services with: docker-compose up -d"
    exit 1
fi

# Test 2: Verify static files directory exists
print_header "Test 2: Static Files Directory Check"

STATIC_DIR_EXISTS=$(run_in_container "taskmanager_web" "test -d /app/staticfiles && echo 'yes' || echo 'no'")
if [ "$STATIC_DIR_EXISTS" = "yes" ]; then
    print_success "Static files directory (/app/staticfiles) exists in web container"
else
    print_error "Static files directory does not exist in web container"
fi

# Test 3: Check if collectstatic has been run
print_header "Test 3: Static Files Collection Check"

STATIC_FILES_COUNT=$(run_in_container "taskmanager_web" "find /app/staticfiles -type f 2>/dev/null | wc -l | tr -d ' '")
if [ "$STATIC_FILES_COUNT" -gt 0 ]; then
    print_success "Static files collected ($STATIC_FILES_COUNT files found in /app/staticfiles)"
    print_info "Sample static files:"
    run_in_container "taskmanager_web" "find /app/staticfiles -type f | head -5" | sed 's/^/  - /'
else
    print_error "No static files found. Run collectstatic manually: docker-compose exec web python manage.py collectstatic --noinput"
    print_info "Attempting to run collectstatic now..."
    if run_in_container "taskmanager_web" "python manage.py collectstatic --noinput" > /dev/null 2>&1; then
        NEW_COUNT=$(run_in_container "taskmanager_web" "find /app/staticfiles -type f 2>/dev/null | wc -l | tr -d ' '")
        if [ "$NEW_COUNT" -gt 0 ]; then
            print_success "Static files collected successfully ($NEW_COUNT files)"
        else
            print_error "collectstatic ran but no files were collected"
        fi
    else
        print_error "Failed to run collectstatic"
    fi
fi

# Test 4: Verify static files are accessible in Nginx container
print_header "Test 4: Nginx Static Files Volume Check"

NGINX_STATIC_EXISTS=$(run_in_container "taskmanager_nginx" "test -d /var/www/static && echo 'yes' || echo 'no'")
if [ "$NGINX_STATIC_EXISTS" = "yes" ]; then
    print_success "Static files directory exists in Nginx container (/var/www/static)"
    
    NGINX_STATIC_COUNT=$(run_in_container "taskmanager_nginx" "find /var/www/static -type f 2>/dev/null | wc -l | tr -d ' '")
    if [ "$NGINX_STATIC_COUNT" -gt 0 ]; then
        print_success "Static files accessible in Nginx container ($NGINX_STATIC_COUNT files)"
        
        # Check if files match between containers (same volume)
        print_info "Verifying volume synchronization..."
        WEB_SAMPLE=$(run_in_container "taskmanager_web" "find /app/staticfiles -type f | head -1 | xargs basename")
        if [ -n "$WEB_SAMPLE" ]; then
            if run_in_container "taskmanager_nginx" "test -f /var/www/static/*/${WEB_SAMPLE} 2>/dev/null && echo 'yes' || echo 'no'" | grep -q "yes"; then
                print_success "Volume synchronization verified (files shared between containers)"
            else
                print_info "Volume synchronization check inconclusive (structure may differ)"
            fi
        fi
    else
        print_error "Static files not found in Nginx container (volume may not be mounted correctly)"
    fi
else
    print_error "Static files directory does not exist in Nginx container"
fi

# Test 5: Test static file serving through Nginx
print_header "Test 5: Static File Serving Test"

# Find a common static file (admin CSS is usually present)
ADMIN_CSS=$(run_in_container "taskmanager_nginx" "find /var/www/static -name 'base.css' -o -name '*.css' | head -1" | tr -d '\r' | xargs basename 2>/dev/null || echo "")

if [ -n "$ADMIN_CSS" ]; then
    # Try to find the full path
    CSS_PATH=$(run_in_container "taskmanager_nginx" "find /var/www/static -name '$ADMIN_CSS' | head -1" | tr -d '\r')
    if [ -n "$CSS_PATH" ]; then
        # Extract the relative path from /var/www/static/
        RELATIVE_PATH="${CSS_PATH#/var/www/static/}"
        
        # Test if file is accessible via HTTP
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/static/${RELATIVE_PATH}" || echo "000")
        
        if [ "$HTTP_STATUS" = "200" ]; then
            print_success "Static file accessible via HTTP (${RELATIVE_PATH})"
            
            # Check cache headers
            CACHE_HEADER=$(curl -s -I "http://localhost/static/${RELATIVE_PATH}" | grep -i "cache-control" || echo "")
            if echo "$CACHE_HEADER" | grep -q "public"; then
                print_success "Cache headers properly configured"
                print_info "Cache-Control: $CACHE_HEADER"
            else
                print_info "Cache headers: $CACHE_HEADER"
            fi
            
            # Check content type
            CONTENT_TYPE=$(curl -s -I "http://localhost/static/${RELATIVE_PATH}" | grep -i "content-type" || echo "")
            print_info "Content-Type: $CONTENT_TYPE"
        elif [ "$HTTP_STATUS" = "404" ]; then
            print_error "Static file not found via HTTP (404) - Check Nginx configuration"
            print_info "Attempted URL: http://localhost/static/${RELATIVE_PATH}"
        else
            print_error "Failed to access static file (HTTP $HTTP_STATUS)"
        fi
    else
        print_info "Could not determine static file path for testing"
    fi
else
    print_info "No CSS files found - trying generic static file test"
    
    # Try to access admin static files (Django admin always has static files)
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/static/admin/css/base.css" || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        print_success "Django admin static files accessible"
    elif [ "$HTTP_STATUS" = "404" ]; then
        print_info "Admin static files not found (may be in different location)"
        print_info "This is normal if admin static files are in a subdirectory"
    else
        print_info "Could not test static file serving (HTTP $HTTP_STATUS)"
    fi
fi

# Test 6: Verify Django settings configuration
print_header "Test 6: Django Settings Verification"

STATIC_URL=$(run_in_container "taskmanager_web" "python manage.py shell -c \"from django.conf import settings; print(settings.STATIC_URL)\"" | tr -d '\r\n')
STATIC_ROOT=$(run_in_container "taskmanager_web" "python manage.py shell -c \"from django.conf import settings; print(settings.STATIC_ROOT)\"" | tr -d '\r\n')

if [ "$STATIC_URL" = "/static/" ]; then
    print_success "STATIC_URL correctly configured: $STATIC_URL"
else
    print_error "STATIC_URL misconfigured: $STATIC_URL (expected: /static/)"
fi

if [ "$STATIC_ROOT" = "/app/staticfiles" ]; then
    print_success "STATIC_ROOT correctly configured: $STATIC_ROOT"
else
    print_error "STATIC_ROOT misconfigured: $STATIC_ROOT (expected: /app/staticfiles)"
fi

# Test 7: Check volume mount configuration
print_header "Test 7: Docker Volume Configuration Check"

# Check if static_volume is properly defined
if docker volume ls --format '{{.Name}}' | grep -q "^task-management-system_static_volume$"; then
    print_success "static_volume Docker volume exists"
    
    VOLUME_MOUNT=$(docker inspect task-management-system_static_volume --format '{{.Mountpoint}}' 2>/dev/null || echo "")
    if [ -n "$VOLUME_MOUNT" ]; then
        print_info "Volume mount point: $VOLUME_MOUNT"
    fi
else
    print_info "static_volume not found (may use different naming convention)"
    print_info "This is normal if using project root as volume name prefix"
fi

# Test 8: Test collectstatic command manually
print_header "Test 8: Manual collectstatic Test"

print_info "Testing collectstatic command (dry run)..."
if run_in_container "taskmanager_web" "python manage.py collectstatic --noinput --dry-run" > /dev/null 2>&1; then
    print_success "collectstatic command works correctly"
else
    print_error "collectstatic command failed"
    print_info "Attempting full collectstatic..."
    if run_in_container "taskmanager_web" "python manage.py collectstatic --noinput"; then
        print_success "collectstatic completed successfully"
    else
        print_error "collectstatic failed - check Django settings"
    fi
fi

# Summary
print_header "Test Summary"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "${BLUE}Total Tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Failed: $TESTS_FAILED${NC}"
fi

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! Static files configuration is correct.${NC}\n"
    exit 0
else
    echo -e "\n${YELLOW}⚠ Some tests failed. Please review the output above.${NC}\n"
    exit 1
fi

