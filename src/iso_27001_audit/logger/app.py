from .base import BaseLogger


class AppLogger(BaseLogger):
    """
    Standard application logger. Uses module __name__.
    """

    def __init__(self, module_name):
        super().__init__(module_name)