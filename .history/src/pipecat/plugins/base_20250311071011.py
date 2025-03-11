"""
Base plugin system components.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import importlib
import inspect
import pkgutil
from typing import Dict, List, Type, TypeVar, Generic, Optional, Any, Set


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


T = TypeVar('T')

@dataclass
class Plugin(ABC, Generic[T]):
    """Base class for all plugins."""
    
    name: str
    version: str
    description: str = ""
    author: str = ""
    
    @abstractmethod
    def initialize(self, app: Any) -> None:
        """Initialize the plugin with the application."""
        pass
    
    def cleanup(self) -> None:
        """Clean up resources when the plugin is disabled."""
        pass


class PluginManager:
    """Manages the discovery, loading and lifecycle of plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._enabled_plugins: Set[str] = set()
    
    def register_plugin_class(self, plugin_class: Type[Plugin]) -> None:
        """Register a plugin class."""
        if not issubclass(plugin_class, Plugin):
            raise PluginError(f"{plugin_class.__name__} is not a subclass of Plugin")
        
        # Create a temporary instance to get the name
        plugin = plugin_class(name=plugin_class.__name__, version="0.0.0")
        self._plugin_classes[plugin.name] = plugin_class
    
    def load_plugin(self, name: str, **kwargs) -> Plugin:
        """Load and initialize a plugin by name."""
        if name in self._plugins:
            return self._plugins[name]
        
        if name not in self._plugin_classes:
            raise PluginError(f"No plugin registered with name: {name}")
        
        plugin_class = self._plugin_classes[name]
        plugin = plugin_class(**kwargs)
        self._plugins[name] = plugin
        return plugin
    
    def enable_plugin(self, name: str, app: Any) -> None:
        """Enable a plugin."""
        if name not in self._plugins:
            self.load_plugin(name)
        
        plugin = self._plugins[name]
        plugin.initialize(app)
        self._enabled_plugins.add(name)
    
    def disable_plugin(self, name: str) -> None:
        """Disable a plugin."""
        if name not in self._plugins or name not in self._enabled_plugins:
            return
        
        plugin = self._plugins[name]
        plugin.cleanup()
        self._enabled_plugins.remove(name)
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """Get all loaded plugins."""
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> List[Plugin]:
        """Get all enabled plugins."""
        return [self._plugins[name] for name in self._enabled_plugins]
    
    def is_plugin_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        return name in self._enabled_plugins


# Default plugin manager instance
default_manager = PluginManager()
