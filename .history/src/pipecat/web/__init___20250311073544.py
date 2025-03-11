"""
Web interfaces for Pipecat.

This module provides web-based interfaces for visualizing and interacting 
with Pipecat pipelines, including dashboards, monitoring tools, and APIs.
"""

from .server import WebServer
from .dashboard import Dashboard, DashboardConfig
from .visualization import PipelineVisualizer

__all__ = ["WebServer", "Dashboard", "DashboardConfig", "PipelineVisualizer"]
