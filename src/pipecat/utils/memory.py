"""
Memory management utilities for OOM protection.
"""
import os
import gc
import sys
import logging
from functools import wraps
from typing import Optional, Callable, Dict, Any, TypeVar, cast

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for generic function decorator
F = TypeVar('F', bound=Callable[..., Any])

class MemoryMonitor:
    """Monitor and manage memory usage to prevent OOM errors."""
    
    def __init__(self, 
                 threshold_percent: float = 90.0,
                 critical_percent: float = 95.0,
                 check_interval: int = 1000,
                 enable_warnings: bool = True):
        """
        Initialize the memory monitor.
        
        Args:
            threshold_percent: Memory usage percentage that triggers warnings
            critical_percent: Memory usage percentage that triggers emergency GC
            check_interval: How often to check memory (in function calls)
            enable_warnings: Whether to log warnings about high memory usage
        """
        self.threshold_percent = threshold_percent
        self.critical_percent = critical_percent
        self.check_interval = check_interval
        self.enable_warnings = enable_warnings
        self.call_count = 0
        
        # Get the process for memory monitoring
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
            logger.warning("psutil not available - memory monitoring will be limited")
    
    def check_memory(self, force: bool = False) -> Dict[str, float]:
        """
        Check current memory usage and take action if needed.
        
        Args:
            force: Whether to force a check regardless of interval
            
        Returns:
            Dict with memory stats: percent used, available MB, total MB
        """
        # Only check memory every check_interval calls unless forced
        self.call_count += 1
        if not force and (self.call_count % self.check_interval != 0):
            return {}
        
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}
        
        # Get memory information
        try:
            vm = psutil.virtual_memory()
            percent_used = vm.percent
            available_mb = vm.available / (1024 * 1024)
            total_mb = vm.total / (1024 * 1024)
            
            # Check if we're approaching memory limit
            if percent_used >= self.critical_percent:
                logger.warning(f"CRITICAL memory usage: {percent_used:.1f}% - Performing emergency cleanup")
                self.reduce_memory_usage(aggressive=True)
            elif percent_used >= self.threshold_percent and self.enable_warnings:
                logger.warning(f"HIGH memory usage: {percent_used:.1f}% - Available: {available_mb:.1f}MB")
                self.reduce_memory_usage(aggressive=False)
            
            return {
                "percent_used": percent_used,
                "available_mb": available_mb,
                "total_mb": total_mb
            }
        except Exception as e:
            logger.error(f"Error monitoring memory: {e}")
            return {"error": str(e)}
    
    def reduce_memory_usage(self, aggressive: bool = False) -> None:
        """
        Attempt to free memory.
        
        Args:
            aggressive: Whether to use more aggressive memory reduction strategies
        """
        # Run garbage collection
        collected = gc.collect(2)
        logger.debug(f"Garbage collection freed {collected} objects")
        
        if aggressive:
            # More aggressive memory reduction for critical situations
            # Clear caches and release as much memory as possible
            self._clear_caches()
    
    def _clear_caches(self) -> None:
        """Clear caches to free memory."""
        # Clear Python's internal caches that might hold memory
        if hasattr(sys, 'getsizeof'):
            gc.collect()
            
            # Try to clear any caches in the codebase
            try:
                # Import here to avoid circular imports
                from ..optimization.caching import clear_all_memory_caches
                clear_all_memory_caches()
                logger.info("Cleared memory caches")
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to clear caches: {e}")


def memory_managed(threshold_mb: Optional[float] = None) -> Callable[[F], F]:
    """
    Decorator to manage memory usage in functions that might use large amounts.
    
    Args:
        threshold_mb: Memory threshold in MB to trigger cleanup after function
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not PSUTIL_AVAILABLE:
                return func(*args, **kwargs)
                
            # Check memory before function execution
            monitor = MemoryMonitor()
            pre_stats = monitor.check_memory(force=True)
            pre_memory = pre_stats.get("available_mb", 0)
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Check memory after function execution
            post_stats = monitor.check_memory(force=True)
            post_memory = post_stats.get("available_mb", 0)
            
            # Calculate memory difference
            memory_diff = pre_memory - post_memory if pre_memory and post_memory else 0
            
            # If memory usage increased beyond threshold or is high, cleanup
            if (threshold_mb and memory_diff > threshold_mb) or post_stats.get("percent_used", 0) > 80:
                logger.debug(f"Function {func.__name__} used {memory_diff:.1f}MB of memory")
                monitor.reduce_memory_usage()
                
            return result
        
        return cast(F, wrapper)
    
    return decorator


# Create a global memory monitor instance
global_memory_monitor = MemoryMonitor()

def update_cache_clearing_function():
    """Update the cache clearing function to handle all registered caches."""
    try:
        from ..optimization.caching import clear_all_memory_caches
    except ImportError:
        logger.warning("Could not import caching module")
