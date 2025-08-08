"""
Logging configuration for the application.
Provides structured logging with proper formatting and rotation.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors."""
        if not hasattr(record, 'color'):
            record.color = self.COLORS.get(record.levelname, '')
        if not hasattr(record, 'reset'):
            record.reset = self.RESET
        
        return super().format(record)


def setup_logging() -> logging.Logger:
    """Set up application logging configuration."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(level=logging.WARNING)
    
    # Create application logger
    logger = logging.getLogger("goldleaves")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    logger.propagate = False
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with colors (for development)
    if settings.is_development:
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = "%(color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(message)s"
        console_formatter = ColoredFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    # JSON handler for structured logging (production)
    if settings.is_production:
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.json",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        json_formatter = JSONFormatter()
        json_handler.setFormatter(json_formatter)
        logger.addHandler(json_handler)
    
    # Set up third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )
    
    return logger


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'exc_info', 'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class RequestIDFilter(logging.Filter):
    """Filter to add request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to record if available."""
        # This would be set by middleware in a real application
        record.request_id = getattr(record, 'request_id', 'N/A')
        return True


# Backward compatibility
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = logging.INFO


def get_logger(name: str) -> logging.Logger:
    """Legacy function for backward compatibility."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
    return logger


# Create logger instance
logger = setup_logging()
