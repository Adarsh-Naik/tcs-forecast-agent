"""
Custom Logger Utilities
Provides additional logging functionality
"""
import logging
from app.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Setup a configured logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Create console handler with formatting
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger