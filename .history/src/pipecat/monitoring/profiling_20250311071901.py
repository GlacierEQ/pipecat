"""
Profiling utilities for Pipecat applications.
"""
import cProfile
import pstats
import io
import time
from functools import wraps
from typing import Callable, Any, Optional, Dict, List, Union
import contextlib


class Profiler:
    """Profile code execution and report performance metrics."""
    
    def __init__(self, 
                 name: str = "pipecat_profile", 
                 enabled: bool = True,
                 include_memory: bool = False):
        self.name = name
        self.enabled = enabled
        self.include_memory = include_memory
        self.profiler = cProfile.Profile()
        self.start_time = None
        
    def __enter__(self):
        if self.enabled:
            self.start_time = time.time()
            self.profiler.enable()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled:
            self.profiler.disable()
            self.duration = time.time() - self.start_time
    
    def print_stats(self, 
                   sort_by: str = "cumulative", 
                   limit: int = 20,
                   output_file: Optional[str] = None) -> None:
        """
        Print profiling statistics.
        
        Args:
            sort_by: Field to sort by (e.g. 'cumulative', 'time', 'calls')
            limit: Number of lines to print
            output_file: Path to write stats to (if None, prints to stdout)
        """
        if not self.enabled:
            print("Profiling was disabled")
            return
        
        # Create a string stream to capture the output
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)
        ps.print_stats(limit)
        
        # Get the captured output
        stats_str = s.getvalue()
        
        # Append total time
        stats_str += f"\nTotal time: {self.duration:.3f} seconds\n"
        
        # Print or save the output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(stats_str)
        else:
            print(stats_str)
    
    @staticmethod
    def profile_function(name: Optional[str] = None, 
                        enabled: bool = True,
                        sort_by: str = "cumulative",
                        limit: int = 20):
        """
        Decorator for profiling a function.
        
        Args:
            name: Profile name (defaults to function name)
            enabled: Whether profiling is enabled
            sort_by: Field to sort by in the report
            limit: Number of lines to print
            
        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                profile_name = name or func.__name__
                with Profiler(name=profile_name, enabled=enabled) as profiler:
                    result = func(*args, **kwargs)
                
                if enabled:
                    profiler.print_stats(sort_by=sort_by, limit=limit)
                
                return result
            return wrapper
        return decorator


@contextlib.contextmanager
def profile_block(name: str = "code_block", 
                 enabled: bool = True,
                 sort_by: str = "cumulative",
                 limit: int = 20):
    """
    Context manager for profiling a block of code.
    
    Args:
        name: Profile name
        enabled: Whether profiling is enabled
        sort_by: Field to sort by in the report
        limit: Number of lines to print
        
    Yields:
        Profiler instance
    """
    profiler = Profiler(name=name, enabled=enabled)
    profiler.__enter__()
    try:
        yield profiler
    finally:
        profiler.__exit__(None, None, None)
        if enabled:
            profiler.print_stats(sort_by=sort_by, limit=limit)
