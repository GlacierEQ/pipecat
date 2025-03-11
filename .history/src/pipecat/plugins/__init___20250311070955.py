"""
Plugin system for Pipecat.

This module provides a plugin architecture that allows extending
Pipecat functionality through discoverable plugins.
"""

from .base import Plugin, PluginManager, PluginError
from .discovery import discover_plugins

__all__ = ["Plugin", "PluginManager", "PluginError", "discover_plugins"]
