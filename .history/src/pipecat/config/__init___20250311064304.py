"""
Configuration management for pipecat.

This module handles loading, validation, and management of configuration settings
for pipecat applications, including environment variables, defaults, and overrides.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PipecatConfig:
    """Central configuration class for pipecat applications."""
    
    debug: bool = False
    log_level: str = "INFO"
    cache_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls, prefix: str = "PIPECAT_") -> "PipecatConfig":
        """Create a config instance from environment variables."""
        config = cls()
        
        if f"{prefix}DEBUG" in os.environ:
            config.debug = os.environ[f"{prefix}DEBUG"].lower() in ("true", "1", "yes")
        
        if f"{prefix}LOG_LEVEL" in os.environ:
            config.log_level = os.environ[f"{prefix}LOG_LEVEL"]
            
        if f"{prefix}CACHE_DIR" in os.environ:
            config.cache_dir = os.environ[f"{prefix}CACHE_DIR"]
            
        return config


# Default config instance
default_config = PipecatConfig.from_env()

__all__ = ["PipecatConfig", "default_config"]
