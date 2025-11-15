"""
Centralized Logging Utility for Tamil AI Voice Assistant

Provides consistent logging configuration across all modules
with support for structured logging and audit trail integration.
"""

import logging
import sys
from typing import Optional
from datetime import datetime
import json

from backend.settings import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for production
    and readable text logs for development.
    """

    def __init__(self, use_json: bool = False):
        super().__init__()
        self.use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as either JSON or text."""

        if self.use_json:
            # Structured JSON logging for production
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }

            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            # Add extra fields from the record
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                              'filename', 'module', 'lineno', 'funcName', 'created',
                              'msecs', 'relativeCreated', 'thread', 'threadName',
                              'processName', 'process', 'message', 'exc_info', 'exc_text',
                              'stack_info', 'getMessage']:
                    log_data[key] = value

            return json.dumps(log_data, default=str)

        else:
            # Human-readable text logging for development
            timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

            # Color coding for different log levels
            colors = {
                'DEBUG': '\033[36m',     # Cyan
                'INFO': '\033[32m',      # Green
                'WARNING': '\033[33m',   # Yellow
                'ERROR': '\033[31m',     # Red
                'CRITICAL': '\033[41m',  # Red background
            }
            reset = '\033[0m'

            color = colors.get(record.levelname, '')

            formatted = f"{timestamp} | {color}{record.levelname:8}{reset} | {record.name:30} | {record.getMessage()}"

            # Add exception info if present
            if record.exc_info:
                formatted += f"\n{self.formatException(record.exc_info)}"

            return formatted


def setup_logging(
    level: str = "INFO",
    use_json: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Setup application-wide logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use structured JSON logging
        log_file: Optional file path to also log to file
    """

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = StructuredFormatter(use_json=use_json)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(numeric_level)

    # Optional file handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    # Set library loggers to WARNING to reduce noise
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for the given name.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Ensure logger has proper level if not already configured
    if not logger.handlers and not logger.parent.handlers:
        # Fallback configuration if setup_logging wasn't called
        handler = logging.StreamHandler()
        formatter = StructuredFormatter(use_json=False)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_audit_event(
    logger: logging.Logger,
    action: str,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    additional_data: Optional[dict] = None
) -> None:
    """
    Log an audit event with structured data.

    This is a convenience function for logging audit events that will be
    captured by both regular logging and the audit service.
    """

    audit_data = {
        "audit_event": True,
        "action": action,
        "user_id": user_id,
        "organization_id": organization_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat()
    }

    if additional_data:
        audit_data.update(additional_data)

    # Log with extra fields that will be picked up by structured formatter
    logger.info(f"Audit event: {action}", extra=audit_data)


# Initialize logging on import if not already configured
if not logging.getLogger().handlers:
    # Auto-configure based on environment
    try:
        log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
        use_json_logging = getattr(settings, 'USE_JSON_LOGGING', False)
        log_file = getattr(settings, 'LOG_FILE', None)

        setup_logging(
            level=log_level,
            use_json=use_json_logging,
            log_file=log_file
        )
    except Exception:
        # Fallback to basic configuration if settings are not available
        setup_logging(level='INFO', use_json=False)


# Module-level convenience functions
def get_audit_logger(name: str) -> logging.Logger:
    """Get a logger specifically configured for audit events."""
    return get_logger(f"audit.{name}")


def get_security_logger(name: str) -> logging.Logger:
    """Get a logger specifically configured for security events."""
    return get_logger(f"security.{name}")


def get_performance_logger(name: str) -> logging.Logger:
    """Get a logger specifically configured for performance monitoring."""
    return get_logger(f"performance.{name}")


# Export main functions
__all__ = [
    'get_logger',
    'get_audit_logger',
    'get_security_logger',
    'get_performance_logger',
    'setup_logging',
    'log_audit_event',
    'StructuredFormatter'
]