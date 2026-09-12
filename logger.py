"""Logging setup for Arc NFT Whitelist Hunter."""
from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Root logger for our app
    logger = logging.getLogger("arc_wl_hunter")
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
