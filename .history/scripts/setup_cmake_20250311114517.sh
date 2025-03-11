#!/bin/bash
# Automatically sets up the optimized CMake environment

# Determine CPU count for parallel builds with max 12
if [ -e /proc/cpuinfo ]; then
    CPUS=$(grep -c ^processor /proc/cpuinfo)
elif [ "$(uname)" == "Darwin" ]; then
    CPUS=$(sysctl -n hw.ncpu)
else
    CPUS=8
fi

# Limit to 12 cores maximum
if [ $CPUS -gt 12 ]; then
    CPUS=12
fi

# Set CMake environment variables
export CMAKE_BUILD_PARALLEL_LEVEL=$CPUS
export NINJA_STATUS="[%p|%f/%t] [%es] "
export NINJA_MAX_JOBS=$CPUS

# Optimize ccache
export CCACHE_NODIRECT=true
export CCACHE_SLOPPINESS=pch_defines,time_macros,include_file_mtime,include_file_ctime
export CCACHE_COMPRESS=true
export CCACHE_COMPRESSLEVEL=6
export CCACHE_MAXSIZE=5G

# Check for ninja and ccache with optimized configuration
if ! command -v ninja &> /dev/null; then
    echo "Installing optimized ninja build system..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install ninja
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update && sudo apt-get install -y ninja-build
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y ninja-build
    fi
    
    # Configure Ninja for optimal performance
    mkdir -p ~/.ninja
    echo "ninja_required_version = 1.11.1" > ~/.ninja/ninja.conf
    echo "parallelism = $CPUS" >> ~/.ninja/ninja.conf
    echo "jobsflag = -j$CPUS" >> ~/.ninja/ninja.conf
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

# Configure and build with optimal settings
echo "Configuring optimized CMake build..."
mkdir -p build/Release
cd build/Release

# Advanced CMake configuration with optimization flags
cmake ../.. -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DBUILD_TESTING=ON \
    -DBUILD_BENCHMARKS=ON \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_BUILD_PARALLEL_LEVEL=$CPUS \
    -DCMAKE_JOB_POOLS="compile=$CPUS;link=4" \
    -DCMAKE_JOB_POOL_COMPILE=compile \
    -DCMAKE_JOB_POOL_LINK=link \
    -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON

# Build with enhanced Ninja settings
echo "Building with optimized Ninja configuration..."
cmake --build . --parallel $CPUS --target all -- -j $CPUS

echo "CMake optimized setup complete!"

# Copy compile_commands.json to project root for tools like clangd
cp compile_commands.json ../../
