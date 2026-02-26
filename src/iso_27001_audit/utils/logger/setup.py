import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from .formatters import JsonFormatter, PrettyFormatter
from .settings import LoggerSettings


def _parse_level(level_str):
    return getattr(logging, level_str, logging.INFO)


def setup_logging(settings=None):
    """
    Configure ROOT logging once.
    Call this exactly once at application start.
    """

    if settings is None:
        settings = LoggerSettings()

    level = _parse_level(settings.level)

    root = logging.getLogger()
    root.setLevel(level)

    # remove existing handlers (uvicorn reload / repeated imports)
    root.handlers.clear()

    # formatter selection
    formatter = JsonFormatter(settings.app_name) if settings.json_logs else PrettyFormatter(settings.app_name)

    # stdout handler (Docker best practice)
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(level)
    stdout.setFormatter(formatter)
    root.addHandler(stdout)

    # optional file handler
    if settings.log_to_file:
        os.makedirs(settings.log_dir, exist_ok=True)
        file_path = os.path.join(settings.log_dir, settings.log_file)

        file_handler = TimedRotatingFileHandler(
            filename=str(file_path),
            when=settings.rotate_when,
            interval=settings.rotate_interval,
            backupCount=settings.rotate_backup_count,
            encoding="utf-8",
            utc=True,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # quiet noisy libs a bit
    logging.getLogger("httpx").setLevel(logging.WARNING)