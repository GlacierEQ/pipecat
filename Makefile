.PHONY: all build clean test install format lint dev docs benchmark release precommit

# Default target
all: build

# Use Ninja if available, otherwise use make
NINJA := $(shell command -v ninja 2> /dev/null)
CMAKE_GENERATOR := $(if $(NINJA),Ninja,Unix Makefiles)
CMAKE_BUILD_PARALLEL_LEVEL ?= $(shell nproc 2>/dev/null || echo 4)
export CMAKE_BUILD_PARALLEL_LEVEL

# Build type
BUILD_TYPE ?= Release

# Build directory
BUILD_DIR = build/$(BUILD_TYPE)

# Configure the project
configure:
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake ../.. -G "$(CMAKE_GENERATOR)" \
		-DCMAKE_BUILD_TYPE=$(BUILD_TYPE) \
		-DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
		-DBUILD_TESTING=ON

# Build the project
build: configure
	@cmake --build $(BUILD_DIR) --config $(BUILD_TYPE) --parallel $(CMAKE_BUILD_PARALLEL_LEVEL)

# Clean the build directory
clean:
	@rm -rf build/
	@rm -f compile_commands.json
	@find . -name "__pycache__" -type d -exec rm -rf {} +

# Run the tests
test: build
	@pytest --cov=src --cov-report=xml --cov-report=term --asyncio-mode=strict
	@cd $(BUILD_DIR) && ctest --output-on-failure --parallel $(CMAKE_BUILD_PARALLEL_LEVEL)

# Install the project
install: build
	@cmake --install $(BUILD_DIR) --prefix install

# Format code
format:
	@python -m black src tests examples
	@python -m isort src tests examples

# Run linters
lint:
	@python -m ruff check src tests examples
	@python -m mypy src tests examples

# Set up development environment
dev:
	@pip install -e ".[dev,test,docs,extensions]"
	@pre-commit install

# Build documentation
docs:
	@cd docs && make html

# Run benchmarks
benchmark: build
	@cd $(BUILD_DIR) && ctest -R benchmark --output-on-failure

# Create a release package
release: format lint test
	@echo "Release package created in dist/"
	@echo "Release package created in dist/"

# Run pre-commit hooks
precommit:
	@pre-commit run --all-files