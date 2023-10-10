import logging


class SuppressLogging:
    """
    Context manager for suppressing log messages of a given level and above.

    Args:
        logger_name (str): Name of the logger to suppress messages from.
        level (int): Logging level to suppress. Messages of this level and above will be suppressed.

    Example usage:
        with SuppressLogging('root', logging.WARNING):
            logging.warning("This is a warning!")  # This will be suppressed
    """

    def __init__(self, logger_name, level):
        self.logger_name = logger_name
        self.level = level
        self.original_level = None

    def __enter__(self):
        """
        Enter the context, suppressing log messages.
        """
        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        logger.setLevel(logging.CRITICAL)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context, restoring original logging settings.
        """
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.original_level)
