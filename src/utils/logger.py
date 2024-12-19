"""
Logger Utility Module

This module provides a configured logger for consistent logging across the application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Create and configure a logger instance.
    
    Args:
        name: Name of the logger
        level: Logging level
        log_file: Optional path to log file
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger 