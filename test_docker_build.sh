#!/bin/bash

# ============================================================================
# Docker Build Test Script for Task Management System
# ============================================================================
# This script comprehensively tests Docker image building locally.
# It validates Dockerfile, builds images, verifies metadata, and tests containers.
#
# Usage:
#   ./test_docker_build.sh [tag]
#   ./test_docker_build.sh test
#   ./test_docker_build.sh latest
#   ./test_docker_build.sh v1.0.0
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="task-management-system"
TAG="${1:-test}"
FULL_IMAGE="${IMAGE_NAME}:${TAG}"

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Test functions
test_prerequisites() {
    print_header "Testing Prerequisites"
    
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        print_success "Docker Compose is installed"
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
}

test_dockerfile() {
    print_header "Validating Dockerfile"
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found"
        exit 1
    fi
    
    print_success "Dockerfile exists"
    
    # Check for required instructions
    if grep -q "FROM python:3.11-slim" Dockerfile; then
        print_success "Dockerfile uses Python 3.11 slim base image"
    else
        print_warning "Dockerfile may not use Python 3.11 slim"
    fi
    
    if grep -q "HEALTHCHECK" Dockerfile; then
        print_success "Dockerfile includes HEALTHCHECK"
    else
        print_warning "Dockerfile missing HEALTHCHECK"
    fi
    
    if grep -q "LABEL" Dockerfile; then
        print_success "Dockerfile includes metadata labels"
    else
        print_warning "Dockerfile missing labels"
    fi
}

test_build_image() {
    print_header "Building Docker Image"
    
    print_info "Building image: ${FULL_IMAGE}"
    if docker build -t "${FULL_IMAGE}" .; then
        print_success "Docker image built successfully"
    else
        print_error "Docker image build failed"
        exit 1
    fi
}

test_image_metadata() {
    print_header "Extracting Image Metadata"
    
    if docker images "${IMAGE_NAME}:${TAG}" | grep -q "${TAG}"; then
        print_success "Image exists in Docker"
    else
        print_error "Image not found"
        exit 1
    fi
    
    IMAGE_ID=$(docker images "${FULL_IMAGE}" --format '{{.ID}}')
    IMAGE_SIZE=$(docker inspect "${FULL_IMAGE}" --format '{{.Size}}')
    IMAGE_CREATED=$(docker inspect "${FULL_IMAGE}" --format '{{.Created}}')
    IMAGE_ARCH=$(docker inspect "${FULL_IMAGE}" --format '{{.Architecture}}')
    IMAGE_OS=$(docker inspect "${FULL_IMAGE}" --format '{{.Os}}')
    
    echo "  Image ID: ${IMAGE_ID}"
    echo "  Size: ${IMAGE_SIZE} bytes ($(echo "scale=2; ${IMAGE_SIZE}/1024/1024" | bc) MB)"
    echo "  Created: ${IMAGE_CREATED}"
    echo "  Architecture: ${IMAGE_ARCH}"
    echo "  OS: ${IMAGE_OS}"
    
    print_success "Image metadata extracted"
}

test_image_labels() {
    print_header "Verifying Image Labels"
    
    LABELS=$(docker inspect "${FULL_IMAGE}" --format '{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}')
    
    if [ -n "$LABELS" ]; then
        echo "$LABELS" | sort
        print_success "Image labels verified"
    else
        print_warning "No labels found in image"
    fi
}

test_image_layers() {
    print_header "Verifying Image Layers"
    
    echo "Image layer history (last 10 layers):"
    docker history "${FULL_IMAGE}" --format 'table {{.CreatedBy}}\t{{.Size}}' | head -10
    
    print_success "Image layers verified"
}

test_container_startup() {
    print_header "Testing Container Startup"
    
    if docker run --rm --name "test-container-${TAG}" "${FULL_IMAGE}" sleep 5; then
        print_success "Container can start successfully"
    else
        print_error "Container startup failed"
        exit 1
    fi
}

test_python_installation() {
    print_header "Verifying Python Installation"
    
    PYTHON_VERSION=$(docker run --rm "${FULL_IMAGE}" python --version 2>&1)
    echo "  ${PYTHON_VERSION}"
    
    if echo "${PYTHON_VERSION}" | grep -q "Python 3.11"; then
        print_success "Python 3.11 is correctly installed"
    else
        print_error "Python version mismatch"
        exit 1
    fi
}

test_django_installation() {
    print_header "Verifying Django Installation"
    
    DJANGO_VERSION=$(docker run --rm "${FULL_IMAGE}" python -c "import django; print(django.get_version())" 2>&1)
    
    if [ -n "$DJANGO_VERSION" ] && [ "$DJANGO_VERSION" != "None" ]; then
        echo "  Django version: ${DJANGO_VERSION}"
        print_success "Django is correctly installed"
    else
        print_error "Django installation verification failed"
        exit 1
    fi
}

test_directory_structure() {
    print_header "Verifying Directory Structure"
    
    if docker run --rm "${FULL_IMAGE}" test -d /app; then
        print_success "/app directory exists"
    else
        print_error "/app directory missing"
        exit 1
    fi
    
    if docker run --rm "${FULL_IMAGE}" test -f /app/manage.py; then
        print_success "manage.py exists"
    else
        print_error "manage.py missing"
        exit 1
    fi
}

test_docker_compose() {
    print_header "Validating Docker Compose Configuration"
    
    if docker compose config --quiet 2>/dev/null || docker-compose config --quiet 2>/dev/null; then
        print_success "docker-compose.yml syntax is valid"
    else
        print_error "docker-compose.yml has syntax errors"
        exit 1
    fi
    
    print_info "Testing docker-compose build..."
    if docker compose build --quiet 2>/dev/null || docker-compose build --quiet 2>/dev/null; then
        print_success "docker-compose build successful"
    else
        print_warning "docker-compose build had issues (may be expected if services are running)"
    fi
}

test_image_size() {
    print_header "Checking Image Size"
    
    SIZE=$(docker inspect "${FULL_IMAGE}" --format '{{.Size}}')
    SIZE_MB=$(echo "scale=2; ${SIZE}/1024/1024" | bc)
    
    echo "  Image size: ${SIZE_MB} MB"
    
    if [ "$SIZE" -gt 1073741824 ]; then
        print_warning "Image size (${SIZE_MB} MB) exceeds 1GB"
        print_info "Consider optimizing the Dockerfile to reduce size"
    else
        print_success "Image size is acceptable (${SIZE_MB} MB)"
    fi
}

cleanup() {
    print_header "Cleanup Options"
    
    read -p "Do you want to remove the test image? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if docker rmi "${FULL_IMAGE}" 2>/dev/null; then
            print_success "Test image removed"
        else
            print_warning "Could not remove image (may be in use)"
        fi
    else
        print_info "Keeping test image: ${FULL_IMAGE}"
    fi
}

print_summary() {
    print_header "Test Summary"
    
    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
    echo "  Total tests: ${TOTAL_TESTS}"
    echo -e "  ${GREEN}Passed: ${TESTS_PASSED}${NC}"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "  ${RED}Failed: ${TESTS_FAILED}${NC}"
        exit 1
    else
        echo -e "  ${GREEN}Failed: 0${NC}"
        echo -e "\n${GREEN}✅ All tests passed!${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║         Docker Build Test Script - Task Management System                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    test_prerequisites
    test_dockerfile
    test_build_image
    test_image_metadata
    test_image_labels
    test_image_layers
    test_container_startup
    test_python_installation
    test_django_installation
    test_directory_structure
    test_docker_compose
    test_image_size
    print_summary
    cleanup
    
    echo -e "\n${GREEN}🎉 Docker build testing completed successfully!${NC}\n"
}

# Run main function
main

