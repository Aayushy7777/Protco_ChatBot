"""
Logging configuration module.
Provides structured logging with JSON support.
"""

import logging
import logging.config
from pathlib import Path
from pythonjsonlogger import jsonlogger

from .config import settings


def setup_logging():
    """Configure logging for the application."""
    
    # Create logs directory
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Define log file paths
    general_log = settings.LOGS_DIR / "app.log"
    error_log = settings.LOGS_DIR / "error.log"

    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "filename": str(general_log),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "filename": str(error_log),
                "level": "ERROR",
                "maxBytes": 10485760,
                "backupCount": 5,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file", "error_file"],
        },
    }

    logging.config.dictConfig(config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at level {settings.LOG_LEVEL}")
    return logger


# Initialize logger on module import
logger = setup_logging()
