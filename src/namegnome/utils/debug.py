"""Universal debug/logging utility for NameGnome.

Provides debug(), info(), warn(), error() functions for consistent logging.
Debug output is controlled by the NAMEGNOME_DEBUG environment variable.
Logs to console; can be extended to log to file if needed.
"""

import logging
import os
from typing import Optional
import sys

DEBUG_ON = os.getenv("NAMEGNOME_DEBUG", "0") == "1"

_logger: Optional[logging.Logger] = None


def setup_logger():
    global _logger
    if _logger is not None:
        return _logger
    logger = logging.getLogger("namegnome")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if DEBUG_ON else logging.INFO)
    _logger = logger
    return logger


def debug(msg: str) -> None:
    """Log a debug message if debugging is enabled. Always print to stdout if debugging is enabled."""
    if DEBUG_ON:
        setup_logger().debug(msg)
        print(f"[DEBUG] {msg}", file=sys.stdout, flush=True)


def info(msg: str) -> None:
    """Log an info message."""
    setup_logger().info(msg)


def warn(msg: str) -> None:
    """Log a warning message."""
    setup_logger().warning(msg)


def error(msg: str) -> None:
    """Log an error message."""
    setup_logger().error(msg)
