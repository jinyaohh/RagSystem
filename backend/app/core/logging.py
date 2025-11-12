"""
Logging configuration for Financial RAG System.

Provides structured logging with file rotation and console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        # Format the message
        return super().format(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_file_path: Optional[Path] = None,
) -> None:
    """
    Set up application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file_path: Path to log file
    """
    # Use settings as defaults
    log_level = log_level or settings.LOG_LEVEL
    log_to_file = log_to_file if log_to_file is not None else settings.LOG_TO_FILE
    log_file_path = log_file_path or settings.LOG_FILE_PATH

    # Get log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if settings.is_development:
        # Colored output for development
        console_formatter = ColoredFormatter(
            fmt='%(levelname)s     [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Simple output for production
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Ensure log directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(numeric_level)

        # Detailed format for file logs
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}")
    if log_to_file:
        logger.info(f"Log file: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
