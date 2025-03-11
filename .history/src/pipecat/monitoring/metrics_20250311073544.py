"""
Metrics collection and reporting for Pipecat applications.
"""
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Callable
import threading
import json
import statistics


class MetricType(Enum):
    """Types of metrics that can be collected."""
    
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    TIMER = auto()


@dataclass
class Metric:
    """A single metric measurement."""
    
    name: str
    value: Union[int, float]
    type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects and reports metrics for Pipecat applications."""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self._lock = threading.Lock()
        self.reporters: List[Callable[[Dict[str, List[Metric]]], None]] = []
    
    def record(self, metric: Metric) -> None:
        """Record a new metric."""
        with self._lock:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = []
            self.metrics[metric.name].append(metric)
    
    def counter(self, name: str, increment: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        self.record(Metric(
            name=name,
            value=increment,
            type=MetricType.COUNTER,
            tags=tags or {}
        ))
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric."""
        self.record(Metric(
            name=name,
            value=value,
            type=MetricType.GAUGE,
            tags=tags or {}
        ))
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        self.record(Metric(
            name=name,
            value=value,
            type=MetricType.HISTOGRAM,
            tags=tags or {}
        ))
    
    def timer(self) -> 'Timer':
        """Create a timer for measuring execution time."""
        return Timer(self)
    
    def add_reporter(self, reporter: Callable[[Dict[str, List[Metric]]], None]) -> None:
        """Add a reporter function that will be called with metrics."""
        self.reporters.append(reporter)
    
    def report(self) -> None:
        """Report all collected metrics using registered reporters."""
        with self._lock:
            metrics_copy = {k: list(v) for k, v in self.metrics.items()}
        
        for reporter in self.reporters:
            try:
                reporter(metrics_copy)
            except Exception as e:
                print(f"Error in metrics reporter: {e}")
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collected metrics."""
        stats = {}
        with self._lock:
            for name, metrics in self.metrics.items():
                if not metrics:
                    continue
                
                metric_type = metrics[0].type
                values = [m.value for m in metrics]
                
                if metric_type == MetricType.COUNTER:
                    stats[name] = {"total": sum(values)}
                elif metric_type in (MetricType.GAUGE, MetricType.HISTOGRAM):
                    stats[name] = {
                        "min": min(values),
                        "max": max(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "count": len(values)
                    }
                    if len(values) > 1:
                        stats[name]["stddev"] = statistics.stdev(values)
                
                # Add latest value and timestamp
                latest = metrics[-1]
                stats[name]["latest"] = latest.value
                stats[name]["last_updated"] = latest.timestamp
        
        return stats
    
    def reset(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self.metrics.clear()


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, collector: MetricsCollector, name: str = None, tags: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.name and self.start_time is not None:
            duration = time.time() - self.start_time
            self.collector.record(Metric(
                name=self.name,
                value=duration * 1000,  # Convert to milliseconds
                type=MetricType.TIMER,
                tags=self.tags
            ))


# Create a default metrics collector instance
default_collector = MetricsCollector()

# Add a simple console reporter
def console_reporter(metrics: Dict[str, List[Metric]]) -> None:
    """Report metrics to the console in a readable format."""
    summary = {}
    for name, metric_list in metrics.items():
        if not metric_list:
            continue
            
        metric_type = metric_list[0].type
        values = [m.value for m in metric_list]
        
        if metric_type == MetricType.COUNTER:
            summary[name] = {"type": "counter", "total": sum(values)}
        elif metric_type == MetricType.GAUGE:
            summary[name] = {
                "type": "gauge", 
                "latest": metric_list[-1].value,
                "count": len(values)
            }
        elif metric_type == MetricType.HISTOGRAM:
            summary[name] = {
                "type": "histogram",
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "count": len(values)
            }
        elif metric_type == MetricType.TIMER:
            summary[name] = {
                "type": "timer",
                "min_ms": min(values),
                "max_ms": max(values),
                "mean_ms": statistics.mean(values),
                "count": len(values)
            }
    
    print("\n=== Metrics Summary ===")
    print(json.dumps(summary, indent=2))
    print("======================\n")


default_collector.add_reporter(console_reporter)
