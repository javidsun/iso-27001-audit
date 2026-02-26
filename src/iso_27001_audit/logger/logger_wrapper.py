import logging


class BaseLogger:
    """
    Parent wrapper:
    - Does NOT configure handlers (setup_logging does that).
    - Only returns a named logger.
    """

    def __init__(self, module_name):
        self._logger = logging.getLogger(module_name)

    def get(self):
        return self._logger