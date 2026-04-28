"""
Structured logging configuration
Based on: https://docs.python.org/3/library/logging.html
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "execution_id"):
            log_data["execution_id"] = record.execution_id

        if hasattr(record, "agent"):
            log_data["agent"] = record.agent

        return json.dumps(log_data)


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Setup structured logger

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Get log level from environment or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter if LOG_FORMAT is json, otherwise use standard
    log_format = os.getenv("LOG_FORMAT", "standard")

    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Example usage
if __name__ == "__main__":
    logger = setup_logger(__name__)
    logger.info("Logger initialized")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
