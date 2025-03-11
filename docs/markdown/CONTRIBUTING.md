# Contributing to Pipecat

Thank you for considering contributing to Pipecat! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r dev-requirements.txt

# Install pre-commit hooks
pre-commit install

# Install the package in development mode
pip install -e ".[all]"
```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run the tests:
   ```bash
   pytest
   ```

4. Format and lint your code:
   ```bash
   # Black will automatically format your code
   black .

   # Ruff will check for common issues
   ruff .
   ```

5. Commit your changes:
   ```bash
   git commit -am "Add your meaningful commit message"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a pull request

## Project Structure

The project follows the structure outlined in the [Architecture document](ARCHITECTURE.md).

## Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage

## Documentation

- Update documentation for any changed functionality
- Document new features
- Improve existing documentation where needed
