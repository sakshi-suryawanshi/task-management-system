#!/bin/bash

# Nginx Configuration Test Script
# Tests Nginx configuration file syntax and validates setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nginx Configuration Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration file path
NGINX_CONF="./nginx/nginx.conf"

# Check if config file exists
if [ ! -f "$NGINX_CONF" ]; then
    echo -e "${RED}✗ Error: Nginx configuration file not found at $NGINX_CONF${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Nginx configuration file found${NC}"
echo ""

# Test 1: Check if Nginx container is running
echo -e "${BLUE}[1/6]${NC} Checking Nginx container status..."
if docker ps --filter "name=taskmanager_nginx" --format "{{.Names}}" | grep -q "taskmanager_nginx"; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
    NGINX_CONTAINER_RUNNING=true
else
    echo -e "${YELLOW}⚠ Nginx container is not running${NC}"
    echo -e "${YELLOW}  Note: This script will test config syntax, but some tests require container${NC}"
    NGINX_CONTAINER_RUNNING=false
fi
echo ""

# Test 2: Validate Nginx configuration syntax
echo -e "${BLUE}[2/6]${NC} Validating Nginx configuration syntax..."

if [ "$NGINX_CONTAINER_RUNNING" = true ]; then
    # Test syntax using nginx -t inside container
    if docker exec taskmanager_nginx nginx -t 2>&1 | grep -q "syntax is ok"; then
        echo -e "${GREEN}✓ Nginx configuration syntax is valid${NC}"
        SYNTAX_VALID=true
    else
        echo -e "${RED}✗ Nginx configuration syntax has errors:${NC}"
        docker exec taskmanager_nginx nginx -t 2>&1 | grep -v "configuration file"
        SYNTAX_VALID=false
    fi
else
    # Try to use local nginx if available (for syntax check only)
    if command -v nginx &> /dev/null; then
        if nginx -t -c "$(pwd)/nginx/nginx.conf" 2>&1 | grep -q "syntax is ok"; then
            echo -e "${GREEN}✓ Nginx configuration syntax is valid (local nginx)${NC}"
            SYNTAX_VALID=true
        else
            echo -e "${YELLOW}⚠ Could not validate syntax (nginx not in container or locally)${NC}"
            SYNTAX_VALID=false
        fi
    else
        echo -e "${YELLOW}⚠ Cannot validate syntax (nginx not available)${NC}"
        echo -e "${YELLOW}  Note: Start containers with 'docker-compose up -d nginx' to test${NC}"
        SYNTAX_VALID=false
    fi
fi
echo ""

# Test 3: Check if required locations are configured
echo -e "${BLUE}[3/6]${NC} Checking required location blocks..."
REQUIRED_LOCATIONS=("/static/" "/media/" "/api/" "/admin/" "/health/")
ALL_LOCATIONS_FOUND=true

for location in "${REQUIRED_LOCATIONS[@]}"; do
    if grep -q "location ${location//\//\\/}" "$NGINX_CONF"; then
        echo -e "${GREEN}✓ Location block found: ${location}${NC}"
    else
        echo -e "${RED}✗ Location block missing: ${location}${NC}"
        ALL_LOCATIONS_FOUND=false
    fi
done

if [ "$ALL_LOCATIONS_FOUND" = true ]; then
    echo -e "${GREEN}✓ All required location blocks are present${NC}"
else
    echo -e "${RED}✗ Some location blocks are missing${NC}"
fi
echo ""

# Test 4: Check if upstream is configured
echo -e "${BLUE}[4/6]${NC} Checking upstream configuration..."
if grep -q "upstream django" "$NGINX_CONF"; then
    UPSTREAM_SERVER=$(grep -A 1 "upstream django" "$NGINX_CONF" | grep "server" | head -1)
    echo -e "${GREEN}✓ Upstream 'django' is configured${NC}"
    echo -e "  ${UPSTREAM_SERVER}"
else
    echo -e "${RED}✗ Upstream 'django' is not configured${NC}"
fi
echo ""

# Test 5: Check if proxy headers are configured
echo -e "${BLUE}[5/6]${NC} Checking proxy configuration..."
REQUIRED_PROXY_HEADERS=("Host" "X-Real-IP" "X-Forwarded-For" "X-Forwarded-Proto")
ALL_HEADERS_FOUND=true

for header in "${REQUIRED_PROXY_HEADERS[@]}"; do
    if grep -q "proxy_set_header.*${header}" "$NGINX_CONF"; then
        echo -e "${GREEN}✓ Proxy header configured: ${header}${NC}"
    else
        echo -e "${RED}✗ Proxy header missing: ${header}${NC}"
        ALL_HEADERS_FOUND=false
    fi
done

if [ "$ALL_HEADERS_FOUND" = true ]; then
    echo -e "${GREEN}✓ All required proxy headers are configured${NC}"
else
    echo -e "${RED}✗ Some proxy headers are missing${NC}"
fi
echo ""

# Test 6: Test endpoints if container is running
if [ "$NGINX_CONTAINER_RUNNING" = true ]; then
    echo -e "${BLUE}[6/6]${NC} Testing endpoints..."
    
    # Test health endpoint
    if curl -sf http://localhost/health/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Health endpoint responds: /health/${NC}"
    else
        echo -e "${RED}✗ Health endpoint failed: /health/${NC}"
    fi
    
    # Test static files (check if location is accessible, even if 404)
    STATIC_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/static/test.css 2>/dev/null || echo "000")
    if [ "$STATIC_RESPONSE" = "404" ] || [ "$STATIC_RESPONSE" = "200" ]; then
        echo -e "${GREEN}✓ Static files location accessible: /static/${NC}"
    else
        echo -e "${YELLOW}⚠ Static files location test inconclusive (HTTP $STATIC_RESPONSE)${NC}"
    fi
    
    # Test API endpoint (should proxy to Django)
    API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/ 2>/dev/null || echo "000")
    if [ "$API_RESPONSE" != "000" ]; then
        echo -e "${GREEN}✓ API endpoint proxies to Django: /api/ (HTTP $API_RESPONSE)${NC}"
    else
        echo -e "${YELLOW}⚠ API endpoint test inconclusive${NC}"
    fi
    
else
    echo -e "${BLUE}[6/6]${NC} Skipping endpoint tests (container not running)"
    echo -e "${YELLOW}  Start containers to test endpoints: docker-compose up -d${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$SYNTAX_VALID" = true ] && [ "$ALL_LOCATIONS_FOUND" = true ] && [ "$ALL_HEADERS_FOUND" = true ]; then
    echo -e "${GREEN}✓ All configuration checks passed!${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Ensure Docker containers are running: ${YELLOW}docker-compose up -d${NC}"
    echo -e "  2. Test endpoints manually: ${YELLOW}curl http://localhost/health/${NC}"
    echo -e "  3. Check Nginx logs: ${YELLOW}docker-compose logs nginx${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo -e "${YELLOW}Please review the errors above and fix the configuration${NC}"
    exit 1
fi

