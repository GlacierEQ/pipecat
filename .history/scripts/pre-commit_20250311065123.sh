#!/bin/bash
# pre-commit script to ensure code quality

set -e

# Format with black
echo "Running black..."
black src tests examples

# Run isort
echo "Running isort..."
isort src tests examples

# Run ruff
echo "Running ruff..."
ruff --fix src tests examples

# Run tests
echo "Running tests..."
pytest -xvs tests/
