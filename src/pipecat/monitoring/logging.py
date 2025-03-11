"""
Logging configuration and utilities for Pipecat.
"""
import logging
import sys
from enum import Enum
from typing import Optional, Dict, Any, List, Union
import json
from pathlib import Path


class LogLevel(str, Enum):
    """Log levels supported by Pipecat."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def __init__(self, include_timestamp: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = self.formatTime(record, self.datefmt)
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Include custom fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", 
                "filename", "funcName", "id", "levelname", "levelno", 
                "lineno", "module", "msecs", "message", "msg", "name", 
                "pathname", "process", "processName", "relativeCreated", 
                "stack_info", "thread", "threadName"
            }:
                log_data[key] = value
        
        return json.dumps(log_data)


def configure_logging(
    level: Union[str, LogLevel] = LogLevel.INFO,
    json_format: bool = False,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for Pipecat.
    
    Args:
        level: Log level
        json_format: Whether to format logs as JSON
        log_file: Path to a log file (if None, logs will only go to console)
        log_to_console: Whether to log to console
        logger_name: Name of the logger to configure (if None, root logger is used)
        
    Returns:
        The configured logger
    """
    # Convert string to enum if necessary
    if isinstance(level, str):
        level = LogLevel(level.upper())
    
    # Get the numeric level
    numeric_level = getattr(logging, level.value)
    
    # Get the logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        # Create directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Configure a default logger
default_logger = configure_logging(level=LogLevel.INFO)
