#!/usr/bin/env python3
"""
Benchmark the performance of Pipecat C++ extensions.

This script runs comprehensive benchmarks on the C++ extensions to validate their performance
compared to pure Python implementations.
"""
import sys
import os
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from pipecat.extensions.optimized_processing import process_batch
    from pipecat.extensions.audio_processing import apply_gain
    from pipecat.extensions.tracebacker import profile, start_tracing, stop_tracing, get_traces
    extensions_available = True
except ImportError:
    print("Warning: C++ extensions not available. Running fallback implementations.")
    extensions_available = False

    # Fallback implementations
    def process_batch(data, batch_size=32):
        return [x * 2.0 for x in data]
        
    def apply_gain(audio, gain=1.0):
        return np.array(audio) * gain


def create_test_data(size=1000000):
    """Create test data for benchmarking."""
    return np.random.random(size).astype(np.float32)


@profile
def benchmark_process_batch(data, batch_size=32, iterations=10):
    """Benchmark the process_batch function."""
    results = []
    for _ in range(iterations):
        start_time = time.time()
        result = process_batch(data, batch_size)
        end_time = time.time()
        results.append(end_time - start_time)
    
    return {
        "mean": np.mean(results),
        "std": np.std(results),
        "min": np.min(results),
        "max": np.max(results),
        "iterations": iterations,
        "data_size": len(data),
        "batch_size": batch_size
    }


@profile
def benchmark_apply_gain(data, gain=2.0, iterations=10):
    """Benchmark the apply_gain function."""
    results = []
    for _ in range(iterations):
        start_time = time.time()
        result = apply_gain(data, gain)
        end_time = time.time()
        results.append(end_time - start_time)
    
    return {
        "mean": np.mean(results),
        "std": np.std(results),
        "min": np.min(results),
        "max": np.max(results),
        "iterations": iterations,
        "data_size": len(data),
        "gain": gain
    }


def benchmark_compare_pure_python():
    """Compare C++ extensions to pure Python implementations."""
    # Pure Python implementations
    def py_process_batch(data, batch_size=32):
        return [x * 2.0 for x in data]
        
    def py_apply_gain(audio, gain=1.0):
        return np.array(audio) * gain
    
    # Test data
    data = create_test_data(1000000)
    
    # Benchmark C++ implementations
    start_time = time.time()
    cpp_result = process_batch(data, 32)
    cpp_time = time.time() - start_time
    
    start_time = time.time()
    cpp_gain_result = apply_gain(data, 2.0)
    cpp_gain_time = time.time() - start_time
    
    # Benchmark Python implementations
    start_time = time.time()
    py_result = py_process_batch(data, 32)
    py_time = time.time() - start_time
    
    start_time = time.time()
    py_gain_result = py_apply_gain(data, 2.0)
    py_gain_time = time.time() - start_time
    
    return {
        "process_batch": {
            "cpp": cpp_time,
            "python": py_time,
            "speedup": py_time / cpp_time
        },
        "apply_gain": {
            "cpp": cpp_gain_time,
            "python": py_gain_time,
            "speedup": py_gain_time / cpp_gain_time
        }
    }


def plot_results(results, output_dir=None):
    """Plot benchmark results."""
    plt.figure(figsize=(12, 8))
    
    # Plot process_batch results
    plt.subplot(2, 1, 1)
    plt.bar(['C++ Implementation', 'Python Implementation'], 
            [results['process_batch']['cpp'], results['process_batch']['python']])
    plt.title(f'process_batch Performance (Speedup: {results["process_batch"]["speedup"]:.2f}x)')
    plt.ylabel('Time (seconds)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Plot apply_gain results
    plt.subplot(2, 1, 2)
    plt.bar(['C++ Implementation', 'Python Implementation'], 
            [results['apply_gain']['cpp'], results['apply_gain']['python']])
    plt.title(f'apply_gain Performance (Speedup: {results["apply_gain"]["speedup"]:.2f}x)')
    plt.ylabel('Time (seconds)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(os.path.join(output_dir, 'benchmark_results.png'))
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Benchmark Pipecat C++ extensions")
    parser.add_argument("--iterations", type=int, default=10, 
                        help="Number of iterations for each benchmark")
    parser.add_argument("--data-size", type=int, default=1000000,
                        help="Size of test data")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directory to save benchmark results")
    parser.add_argument("--compare", action="store_true",
                        help="Compare C++ extensions to pure Python implementations")
    args = parser.parse_args()
    
    if not extensions_available:
        print("Warning: Running with fallback implementations. Results will not reflect C++ extension performance.")
    
    # Create test data
    print(f"Creating test data of size {args.data_size}...")
    data = create_test_data(args.data_size)
    
    if args.compare:
        print("Comparing C++ extensions to pure Python implementations...")
        results = benchmark_compare_pure_python()
        
        print("\n=== Benchmark Results ===")
        print(f"process_batch - C++: {results['process_batch']['cpp']:.6f}s, "
              f"Python: {results['process_batch']['python']:.6f}s, "
              f"Speedup: {results['process_batch']['speedup']:.2f}x")
        print(f"apply_gain - C++: {results['apply_gain']['cpp']:.6f}s, "
              f"Python: {results['apply_gain']['python']:.6f}s, "
              f"Speedup: {results['apply_gain']['speedup']:.2f}x")
        
        # Plot results
        plot_results(results, args.output_dir)
    else:
        print(f"Running benchmarks with {args.iterations} iterations...")
        
        # Start tracing if available
        if extensions_available:
            start_tracing()
        
        # Run benchmarks
        batch_results = benchmark_process_batch(data, iterations=args.iterations)
        gain_results = benchmark_apply_gain(data, iterations=args.iterations)
        
        # Stop tracing if available
        if extensions_available:
            stop_tracing()
            traces = get_traces()
            print(f"Collected {len(traces)} traces")
        
        print("\n=== process_batch Results ===")
        print(f"Mean time: {batch_results['mean']:.6f}s")
        print(f"Std deviation: {batch_results['std']:.6f}s")
        print(f"Min time: {batch_results['min']:.6f}s")
        print(f"Max time: {batch_results['max']:.6f}s")
        
        print("\n=== apply_gain Results ===")
        print(f"Mean time: {gain_results['mean']:.6f}s")
        print(f"Std deviation: {gain_results['std']:.6f}s")
        print(f"Min time: {gain_results['min']:.6f}s")
        print(f"Max time: {gain_results['max']:.6f}s")


if __name__ == "__main__":
    main()
