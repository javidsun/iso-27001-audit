import os


class LoggerSettings:
    """
    Read logging settings from environment variables.
    No side effects.
    """

    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "iso-27001-audit")

        # LOG_LEVEL: DEBUG | INFO | WARNING | ERROR
        self.level = os.getenv("LOG_LEVEL", "INFO").upper()

        # LOG_JSON=1 -> JSON logs
        self.json_logs = os.getenv("LOG_JSON", "0") == "1"

        # Optional file logging
        self.log_to_file = os.getenv("LOG_TO_FILE", "0") == "1"
        self.log_dir = os.getenv("LOG_DIR", "logs")
        self.log_file = os.getenv("LOG_FILE", "app.log")

        # Rotation options (daily by default)
        self.rotate_when = os.getenv("LOG_ROTATE_WHEN", "midnight")
        self.rotate_interval = int(os.getenv("LOG_ROTATE_INTERVAL", "1"))
        self.rotate_backup_count = int(os.getenv("LOG_ROTATE_BACKUP_COUNT", "14"))