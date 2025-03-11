"""
TraceBacker: High-performance profiling and tracing tool for Pipecat.

This module provides C++ accelerated performance tracking, call stack tracing,
and profiling tools for Pipecat applications.
"""
import functools
import time
import inspect
from typing import Callable, Dict, List, Optional, Any, Union, TypeVar, cast

try:
    from ._tracebacker import (
        # Tracing functions
        start_tracing, stop_tracing, get_traces, clear_traces, is_tracing,
        trace_function,
        
        # Performance tracking
        enable_tracking, disable_tracking, is_tracking_enabled, 
        record_function, enable_function_sampling, disable_function_sampling,
        get_performance_stats, clear_performance_stats, get_moving_average,
        
        # Classes
        CallStackTracker, PerformanceTracker
    )
    _TRACEBACKER_AVAILABLE = True
except ImportError:
    _TRACEBACKER_AVAILABLE = False
    
    # Fallback Python implementations
    def start_tracing():
        """Start collecting trace data."""
        print("TraceBacker C++ extension not available. Using Python fallback.")
        
    def stop_tracing():
        """Stop collecting trace data."""
        pass
        
    def get_traces():
        """Get all collected traces."""
        return []
        
    def clear_traces():
        """Clear all collected traces."""
        pass
        
    def is_tracing():
        """Check if tracing is active."""
        return False
        
    def trace_function(func):
        """Decorator for tracing function execution."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    # Performance tracking fallbacks
    def enable_tracking():
        """Enable performance tracking."""
        pass
        
    def disable_tracking():
        """Disable performance tracking."""
        pass
        
    def is_tracking_enabled():
        """Check if tracking is enabled."""
        return False
        
    def record_function(name, execution_time):
        """Record function execution time."""
        pass
        
    def enable_function_sampling(name, max_samples=100):
        """Enable sampling for a function."""
        pass
        
    def disable_function_sampling(name):
        """Disable sampling for a function."""
        pass
        
    def get_performance_stats():
        """Get performance statistics."""
        return {}
        
    def clear_performance_stats():
        """Clear performance statistics."""
        pass
        
    def get_moving_average(name, window_size=5):
        """Get moving average of function execution times."""
        return []

# Enhanced decorators that work with or without the C++ extension
T = TypeVar('T', bound=Callable[..., Any])

def profile(func: T) -> T:
    """
    Profile a function and record its execution time.
    
    Args:
        func: The function to profile
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if _TRACEBACKER_AVAILABLE:
            record_function(func.__name__, execution_time)
        
        return result
        
    return cast(T, wrapper)

def trace(func: T) -> T:
    """
    Trace function calls and execution times.
    
    This provides more detailed tracing than profile, including file and line info.
    
    Args:
        func: The function to trace
        
    Returns:
        Decorated function
    """
    if _TRACEBACKER_AVAILABLE:
        return cast(T, trace_function(func))
    
    # Fallback Python implementation
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get source info
        filename = inspect.getfile(func)
        line = inspect.getsourcelines(func)[1]
        print(f"Tracing: {func.__name__} in {filename}:{line}")
        
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        print(f"Function {func.__name__} took {execution_time:.6f} seconds")
        return result
        
    return cast(T, wrapper)

# Module exports
__all__ = [
    # Core tracing
    "start_tracing", "stop_tracing", "get_traces", "clear_traces", "is_tracing",
    # Performance tracking
    "enable_tracking", "disable_tracking", "is_tracking_enabled",
    "record_function", "enable_function_sampling", "disable_function_sampling",
    "get_performance_stats", "clear_performance_stats", "get_moving_average",
    # Decorators
    "profile", "trace",
    # Classes
    "CallStackTracker", "PerformanceTracker" if _TRACEBACKER_AVAILABLE else [],
]
