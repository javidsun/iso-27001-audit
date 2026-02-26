import json
import logging
from datetime import datetime, timezone


class PrettyFormatter(logging.Formatter):
    """
    Human-friendly logs (dev).
    """

    def __init__(self, app_name):
        fmt = f"[%(asctime)s] [%(levelname)s] {app_name} %(name)s - %(message)s"
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")


class JsonFormatter(logging.Formatter):
    """
    JSON logs (prod / log aggregation).
    """

    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name

    def format(self, record):
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "app": self.app_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Optional context (if you add it later via LoggerAdapter/middleware)
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)