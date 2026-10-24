"""Logging configuration module."""

import json
import logging
from logging import Formatter
from typing import Optional


class JSONFormatter(Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        return json.dumps(log_data)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure root logging.

    Args:
        level: Logging level, such as ``INFO`` or ``DEBUG``.
        log_file: Optional path for a JSON-formatted log file.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
