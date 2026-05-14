#!/bin/bash
# Automatically sets up the CMake environment

# Determine CPU count for parallel builds
if [ -e /proc/cpuinfo ]; then
    CPUS=$(grep -c ^processor /proc/cpuinfo)
elif [ "$(uname)" == "Darwin" ]; then
    CPUS=$(sysctl -n hw.ncpu)
else
    CPUS=4
fi

# Set CMake environment variables
export CMAKE_BUILD_PARALLEL_LEVEL=$CPUS
export NINJA_STATUS="[%f/%t] (%e) "

# Check for ninja and ccache
if ! command -v ninja &> /dev/null; then
    echo "Installing ninja build system..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install ninja
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update && sudo apt-get install -y ninja-build
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y ninja-build
    fi
fi

if ! command -v ccache &> /dev/null; then
    echo "Installing ccache..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install ccache
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update && sudo apt-get install -y ccache
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y ccache
    fi
fi

# Configure and build
echo "Configuring CMake..."
mkdir -p build/Release
cd build/Release && cmake ../.. -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

echo "Building with Ninja..."
cmake --build . --parallel $CPUS

echo "CMake setup complete!"

# Copy compile_commands.json to project root for tools like clangd
cp compile_commands.json ../../
