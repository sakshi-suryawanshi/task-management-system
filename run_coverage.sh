#!/bin/bash
# ============================================================================
# Coverage Report Script for Task Management System
# ============================================================================
# This script runs pytest with coverage and generates reports.
# Usage: ./run_coverage.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "Running Test Coverage Analysis"
echo "============================================================================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed. Please install it with:"
    echo "  pip install -r requirements-dev.txt"
    exit 1
fi

# Check if coverage is installed
if ! python3 -c "import coverage" 2>/dev/null; then
    echo "Error: coverage is not installed. Please install it with:"
    echo "  pip install -r requirements-dev.txt"
    exit 1
fi

echo "Running tests with coverage..."
echo ""

# Run pytest with coverage
python3 -m pytest \
    --cov=. \
    --cov-config=.coveragerc \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    --cov-fail-under=80 \
    -v \
    --tb=short \
    "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "============================================================================"
    echo "✓ Coverage report generated successfully!"
    echo "============================================================================"
    echo ""
    echo "Coverage reports:"
    echo "  - Terminal: Shown above"
    echo "  - HTML: htmlcov/index.html"
    echo "  - XML: coverage.xml"
    echo ""
    echo "To view HTML report, open: htmlcov/index.html"
else
    echo ""
    echo "============================================================================"
    echo "✗ Coverage below 80% or tests failed"
    echo "============================================================================"
    exit $EXIT_CODE
fi

