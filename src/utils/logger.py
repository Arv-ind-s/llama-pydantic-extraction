"""
Logging configuration for the extraction pipeline.

Provides a factory function to create pre-configured loggers.
Log level is pulled from config/settings.py (which reads from .env).

Usage:
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing started")
"""
import logging
import sys
from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a configured logger.

    Args:
        name: Logger name, typically __name__ from the calling module.
              This makes log output show which module emitted the message.

    Returns:
        Configured logging.Logger instance with console output.
    """
    logger = logging.getLogger(name)

    # Guard: if this logger was already configured, return it as-is
    # prevents duplicate log lines when get_logger() is called multiple times
    if logger.handlers:
        return logger

    # Set level from settings (e.g. "INFO" → logging.INFO)
    # Falls back to INFO if an invalid level string is configured
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Console handler — sends all log output to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)  # let the logger's level do the filtering

    # Format: "2026-02-14 15:57:50 | INFO     | src.parsers.llama_parser | message"
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
