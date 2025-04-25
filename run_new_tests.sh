#!/bin/bash

# Run tests for the new features and improvements
echo "Running tests for new features and improvements..."

# Make script executable
chmod +x run_new_tests.sh

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Create bin directories if they don't exist (for the tests to pass)
mkdir -p tools/model_comparison/bin
mkdir -p tools/github_pr/bin

# Make script files executable
chmod +x tools/model_comparison/bin/compare_models.py 2>/dev/null || true
chmod +x tools/github_pr/bin/create_pr.py 2>/dev/null || true

# Run pytest on the new test files
echo "Running tests for beginner-friendly configuration..."
python -m pytest tests/test_beginner_config.py -v

echo "Running tests for documentation..."
python -m pytest tests/test_docs.py -v

echo "Running tests for directory structure..."
python -m pytest tests/test_directory_structure.py -v

echo "Running tests for model comparison tool..."
python -m pytest tests/test_model_comparison.py -v

echo "Running tests for GitHub PR tool..."
python -m pytest tests/test_github_pr.py -v

echo "Running tests for error handling..."
python -m pytest tests/test_error_handler.py -v

echo "Running tests for token management..."
python -m pytest tests/test_token_manager.py -v

echo "All tests completed!"