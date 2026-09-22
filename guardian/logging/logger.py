"""Centralized logging system for GuardianAI with secret scrubbing and file/console outputs."""

import logging
import re
import sys
from pathlib import Path
from typing import Optional


class SensitiveDataScrubber(logging.Formatter):
    """Custom logging formatter that scrubs passwords, tokens, API keys, and credentials."""

    SECRET_PATTERNS = [
        (re.compile(r"(?i)(password|passwd|secret|api_key|token|auth_token)\s*=\s*['\"]?([^'\"\s]+)['\"]?"), r"\1=***REDACTED***"),
        (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{10,}"), r"\1***REDACTED***"),
    ]

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        for pattern, replacement in self.SECRET_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
        return formatted

class SafeConsoleHandler(logging.StreamHandler):
    """Console handler that safely handles pytest and redirected stdout."""

    def __init__(self) -> None:
        super().__init__(stream=None)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.stream = sys.stdout
            super().emit(record)
        except (ValueError, OSError):
            # stdout may have been closed by a test capture/redirect.
            pass
                
def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "guardian.log",
    console_output: bool = True
) -> logging.Logger:
    """Initialize and configure GuardianAI central logger."""
    logger = logging.getLogger("GuardianAI")
    logger.handlers.clear()

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = SensitiveDataScrubber(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if console_output:
        console_handler = SafeConsoleHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_dir and log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Retrieve default GuardianAI logger instance."""
    return logging.getLogger("GuardianAI")
