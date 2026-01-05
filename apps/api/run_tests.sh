#!/bin/bash
# Test runner script for service layer tests

set -e

echo "=================================="
echo "Running Service Layer Tests"
echo "=================================="
echo ""

# Check if in correct directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must run from apps/api directory"
    exit 1
fi

# Check if dependencies installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install -e ".[dev]"
    echo ""
fi

# Run tests
echo "Running prerequisite service tests..."
pytest tests/services/test_prerequisite_service.py -v

echo ""
echo "Running requirement service tests..."
pytest tests/services/test_requirement_service.py -v

echo ""
echo "=================================="
echo "Running all service tests with coverage..."
echo "=================================="
pytest tests/services/ -v --cov=app/services --cov-report=term-missing --cov-report=html

echo ""
echo "✓ All tests completed!"
echo "Coverage report generated in htmlcov/index.html"
