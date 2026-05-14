"""
Automation utilities for Pipecat.

This module provides tools for automating common tasks, benchmarking,
and continuous integration/deployment workflows.
"""

from .benchmarks import Benchmark, BenchmarkSuite, BenchmarkResult, run_benchmarks
from .deployment import AutoDeployer, DeploymentConfig
from .reports import ReportGenerator, BenchmarkReportFormat

__all__ = [
    "Benchmark", "BenchmarkSuite", "BenchmarkResult", "run_benchmarks",
    "AutoDeployer", "DeploymentConfig",
    "ReportGenerator", "BenchmarkReportFormat"
]
