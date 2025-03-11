"""
Plugin discovery mechanisms.
"""
import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from typing import List, Type

from .base import Plugin, PluginManager, default_manager


def discover_plugins(package_paths: List[str] = None) -> List[Type[Plugin]]:
    """
    Discover Plugin subclasses from specified packages.
    
    Args:
        package_paths: List of package paths to search for plugins
        
    Returns:
        List of discovered Plugin subclasses
    """
    if package_paths is None:
        # Default to searching in common plugin directories
        package_paths = [
            "pipecat_plugins",
            "pipecat.contrib"
        ]
    
    discovered_plugins = []
    
    for package_path in package_paths:
        try:
            # Try to import the package
            package = importlib.import_module(package_path)
            
            # Walk through the package and its subpackages
            for loader, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
                try:
                    module = importlib.import_module(name)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Check if it's a Plugin subclass but not Plugin itself
                        if (inspect.isclass(attr) and 
                            issubclass(attr, Plugin) and 
                            attr != Plugin):
                            discovered_plugins.append(attr)
                            default_manager.register_plugin_class(attr)
                except ImportError:
                    continue
        except ImportError:
            # Skip packages that aren't installed
            continue
    
    return discovered_plugins


def discover_plugins_from_directory(directory: str) -> List[Type[Plugin]]:
    """
    Discover Plugin subclasses from a directory of Python files.
    
    Args:
        directory: Directory path to search for plugins
        
    Returns:
        List of discovered Plugin subclasses
    """
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        return []
    
    # Add the directory to sys.path temporarily
    original_path = sys.path.copy()
    sys.path.insert(0, str(directory_path))
    
    discovered_plugins = []
    
    try:
        # Iterate through Python files in the directory
        for file_path in directory_path.glob("*.py"):
            module_name = file_path.stem
            
            try:
                # Import the module
                module = importlib.import_module(module_name)
                
                # Find Plugin subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (inspect.isclass(attr) and 
                        issubclass(attr, Plugin) and 
                        attr != Plugin):
                        discovered_plugins.append(attr)
                        default_manager.register_plugin_class(attr)
            except ImportError:
                continue
    finally:
        # Restore the original sys.path
        sys.path = original_path
    
    return discovered_plugins
