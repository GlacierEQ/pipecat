#!/bin/bash
# Script to set up development environment

set -e

echo "Setting up Pipecat development environment..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing development dependencies..."
pip install -r dev-requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Install package in development mode
echo "Installing pipecat in development mode..."
pip install -e ".[all]"

echo "Development environment setup complete!"
echo "You can activate the environment with: source venv/bin/activate"
