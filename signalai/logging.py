"""Utilities for configuring and retrieving loggers.

This module exposes :func:`get_logger` which ensures that the Python
``logging`` module is configured in a consistent way across the project.
Other modules should import ``get_logger`` and create module level loggers
via ``logger = get_logger(__name__)``.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

__all__ = ["configure", "get_logger"]

_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DEFAULT_LEVEL = os.getenv("SIGNALAI_LOG_LEVEL", "INFO")

_configured = False


def configure(level: str = _DEFAULT_LEVEL, fmt: str = _DEFAULT_FORMAT) -> None:
    """Configure the root logger.

    Calling :func:`configure` multiple times has no effect after the first
    invocation to avoid installing duplicate handlers.  The default log level
    can be overridden via the ``SIGNALAI_LOG_LEVEL`` environment variable.
    """
    global _configured
    if _configured:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format=fmt)
    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger with the given name.

    The first call will configure the logging system using
    :func:`configure`.  Subsequent calls simply return a logger instance.
    """
    configure()
    return logging.getLogger(name if name else "signalai")

