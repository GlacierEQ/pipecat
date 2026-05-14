"""
Optimized processing extensions for Pipecat.

This module provides high-performance implementations of computation-intensive
processing operations using C++ and pybind11.
"""
try:
    from ._optimized_processing import process_batch, process_batch_cuda
except ImportError:
    import warnings
    warnings.warn("Optimized processing extensions not available, falling back to Python implementation")
    
    # Fallback Python implementation
    def process_batch(input_data, batch_size=32):
        """Process data in batches (Python fallback implementation)."""
        return [x * 2.0 for x in input_data]
    
    def process_batch_cuda(input_data, batch_size=32):
        """Process data in batches (Python fallback implementation)."""
        return [x * 2.0 for x in input_data]

__all__ = ["process_batch", "process_batch_cuda"]
