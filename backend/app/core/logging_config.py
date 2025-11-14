"""Structured logging configuration with JSON formatter."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add request info if present
        if hasattr(record, 'request_method'):
            log_record['request_method'] = record.request_method
        if hasattr(record, 'request_path'):
            log_record['request_path'] = record.request_path
        if hasattr(record, 'request_ip'):
            log_record['request_ip'] = record.request_ip


def setup_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting (True) or plain text (False)
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if json_logs:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds correlation ID to all log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add correlation ID to log record."""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        if 'correlation_id' in self.extra:
            kwargs['extra']['correlation_id'] = self.extra['correlation_id']
        
        return msg, kwargs


def get_logger(name: str, correlation_id: str = None) -> logging.Logger | LoggerAdapter:
    """
    Get a logger instance with optional correlation ID.
    
    Args:
        name: Logger name (usually __name__)
        correlation_id: Optional correlation ID for request tracking
    
    Returns:
        Logger or LoggerAdapter instance
    """
    logger = logging.getLogger(name)
    
    if correlation_id:
        return LoggerAdapter(logger, {'correlation_id': correlation_id})
    
    return logger
