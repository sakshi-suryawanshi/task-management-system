#!/bin/bash
# ============================================================================
# Code Quality Tools Test Script
# ============================================================================
# This script tests all code quality tools to ensure they are properly
# configured and working correctly.
#
# Usage:
#   chmod +x test_code_quality.sh
#   ./test_code_quality.sh
#
# Requirements:
#   - Python 3.11+
#   - All dependencies from requirements-dev.txt installed
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Function to print header
print_header() {
    echo ""
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((SKIPPED++))
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test tool
test_tool() {
    local tool_name=$1
    local command=$2
    local description=$3
    
    print_info "Testing $tool_name: $description"
    
    if command_exists "$tool_name"; then
        if eval "$command" >/dev/null 2>&1; then
            print_success "$tool_name is working correctly"
            return 0
        else
            print_error "$tool_name test failed"
            return 1
        fi
    else
        print_warning "$tool_name is not installed (skipping)"
        return 2
    fi
}

# Start testing
print_header "Code Quality Tools Test Suite"
print_info "Testing all code quality tools configuration..."
echo ""

# ============================================================================
# 1. Check Python Version
# ============================================================================
print_header "1. Python Version Check"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_info "Python version: $PYTHON_VERSION"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_success "Python version is 3.11 or higher"
else
    print_error "Python version must be 3.11 or higher"
    exit 1
fi

# ============================================================================
# 2. Check Dependencies
# ============================================================================
print_header "2. Dependencies Check"

REQUIRED_PACKAGES=(
    "black"
    "isort"
    "flake8"
    "mypy"
    "pre-commit"
    "bandit"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        VERSION=$(python3 -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        print_success "$package is installed (version: $VERSION)"
    else
        print_error "$package is not installed"
        print_info "Install with: pip install -r requirements-dev.txt"
    fi
done

# ============================================================================
# 3. Test Black Configuration
# ============================================================================
print_header "3. Black Configuration Test"

if command_exists black; then
    print_info "Testing Black configuration..."
    
    # Test Black can read pyproject.toml
    if black --version >/dev/null 2>&1; then
        BLACK_VERSION=$(black --version)
        print_success "Black is working: $BLACK_VERSION"
        
        # Test Black check (dry run)
        if black --check --diff . >/dev/null 2>&1; then
            print_success "Black check passed (code is formatted)"
        else
            print_warning "Black check found formatting issues (run 'black .' to fix)"
        fi
    else
        print_error "Black is not working correctly"
    fi
else
    print_warning "Black is not installed (skipping)"
fi

# ============================================================================
# 4. Test isort Configuration
# ============================================================================
print_header "4. isort Configuration Test"

if command_exists isort; then
    print_info "Testing isort configuration..."
    
    # Test isort can read pyproject.toml
    if isort --version >/dev/null 2>&1; then
        ISORT_VERSION=$(isort --version)
        print_success "isort is working: $ISORT_VERSION"
        
        # Test isort check (dry run)
        if isort --check-only --diff . >/dev/null 2>&1; then
            print_success "isort check passed (imports are sorted)"
        else
            print_warning "isort check found import sorting issues (run 'isort .' to fix)"
        fi
    else
        print_error "isort is not working correctly"
    fi
else
    print_warning "isort is not installed (skipping)"
fi

# ============================================================================
# 5. Test flake8 Configuration
# ============================================================================
print_header "5. flake8 Configuration Test"

if command_exists flake8; then
    print_info "Testing flake8 configuration..."
    
    # Test flake8 can read setup.cfg
    if flake8 --version >/dev/null 2>&1; then
        FLAKE8_VERSION=$(flake8 --version)
        print_success "flake8 is working: $FLAKE8_VERSION"
        
        # Test flake8 on a sample file (non-blocking)
        if flake8 --count --statistics . >/dev/null 2>&1; then
            print_success "flake8 check passed (no linting errors)"
        else
            print_warning "flake8 found linting issues (check output above)"
        fi
    else
        print_error "flake8 is not working correctly"
    fi
else
    print_warning "flake8 is not installed (skipping)"
fi

# ============================================================================
# 6. Test mypy Configuration
# ============================================================================
print_header "6. mypy Configuration Test"

if command_exists mypy; then
    print_info "Testing mypy configuration..."
    
    # Test mypy can read pyproject.toml
    if mypy --version >/dev/null 2>&1; then
        MYPY_VERSION=$(mypy --version)
        print_success "mypy is working: $MYPY_VERSION"
        
        # Test mypy (non-blocking, may have type errors)
        if mypy . --ignore-missing-imports >/dev/null 2>&1; then
            print_success "mypy check passed (no type errors)"
        else
            print_warning "mypy found type issues (non-blocking, check output above)"
        fi
    else
        print_error "mypy is not working correctly"
    fi
else
    print_warning "mypy is not installed (skipping)"
fi

# ============================================================================
# 7. Test Pre-commit Configuration
# ============================================================================
print_header "7. Pre-commit Configuration Test"

if command_exists pre-commit; then
    print_info "Testing pre-commit configuration..."
    
    # Test pre-commit can read .pre-commit-config.yaml
    if pre-commit --version >/dev/null 2>&1; then
        PRE_COMMIT_VERSION=$(pre-commit --version)
        print_success "pre-commit is working: $PRE_COMMIT_VERSION"
        
        # Validate configuration
        if pre-commit validate-config >/dev/null 2>&1; then
            print_success "pre-commit configuration is valid"
        else
            print_error "pre-commit configuration is invalid"
        fi
        
        # Check if hooks are installed
        if [ -f .git/hooks/pre-commit ]; then
            print_success "pre-commit hooks are installed"
        else
            print_warning "pre-commit hooks are not installed (run 'pre-commit install')"
        fi
    else
        print_error "pre-commit is not working correctly"
    fi
else
    print_warning "pre-commit is not installed (skipping)"
fi

# ============================================================================
# 8. Test Configuration Files
# ============================================================================
print_header "8. Configuration Files Check"

CONFIG_FILES=(
    "pyproject.toml"
    ".pre-commit-config.yaml"
    "setup.cfg"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$config_file" ]; then
        print_success "$config_file exists"
    else
        print_error "$config_file is missing"
    fi
done

# ============================================================================
# 9. Test Tool Compatibility
# ============================================================================
print_header "9. Tool Compatibility Check"

# Check if Black and isort are compatible
if command_exists black && command_exists isort; then
    print_info "Checking Black and isort compatibility..."
    
    # Create a test file
    TEST_FILE=$(mktemp /tmp/test_code_quality_XXXXXX.py)
    cat > "$TEST_FILE" << 'EOF'
from django.core.management import execute_from_command_line
from rest_framework import serializers
import os
import sys
EOF
    
    # Test isort with Black profile
    if isort --check-only --profile=black "$TEST_FILE" >/dev/null 2>&1; then
        print_success "Black and isort are compatible"
    else
        print_warning "Black and isort may have compatibility issues"
    fi
    
    # Cleanup
    rm -f "$TEST_FILE"
else
    print_warning "Cannot test compatibility (tools not installed)"
fi

# ============================================================================
# 10. Summary
# ============================================================================
print_header "Test Summary"

TOTAL=$((PASSED + FAILED + SKIPPED))

echo -e "${BLUE}Total tests: $TOTAL${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    print_info "Next steps:"
    echo "  1. Install pre-commit hooks: pre-commit install"
    echo "  2. Run on all files: pre-commit run --all-files"
    echo "  3. Format code: black . && isort ."
    echo "  4. Check linting: flake8 ."
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix the issues above.${NC}"
    echo ""
    print_info "Troubleshooting:"
    echo "  1. Install dependencies: pip install -r requirements-dev.txt"
    echo "  2. Check configuration files are present"
    echo "  3. Verify Python version is 3.11+"
    exit 1
fi

