"""Logging setup — Rotating file + console, no side effects on import."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import (
    LOG_BACKUP_COUNT,
    LOG_FILE,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)


def setup_logging(
    log_file: Path = LOG_FILE,
    level: int = logging.INFO,
    console: bool = True,
) -> None:
    """
    Configure the root logger once.

    Safe to call multiple times (force=True resets handlers).
    Does NOT return a logger — modules use getLogger(__name__).
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT)
    handlers: list[logging.Handler] = []

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)
