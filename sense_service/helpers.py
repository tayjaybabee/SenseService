import logging


from collections import deque

class SensorDataSmoother:
    """
    Class to apply smoothing algorithms to sensor data.

    Usage Example:
        >>> smoother = SensorDataSmoother(method='moving_average', window_size=5)
        >>> smoothed_data = smoother.apply(25.0)
    """

    def __init__(self, method='none', window_size=5, alpha=0.2):
        """
        Initialize the SensorDataSmoother class.

        Parameters:
            method (str): The smoothing method ('none', 'moving_average', 'exponential_moving_average').
            window_size (int): The size of the window for the moving average.
            alpha (float): The smoothing factor for exponential moving average, between 0 and 1.
        """
        self.method = method
        self.window_size = window_size
        self.alpha = alpha
        self.data = deque(maxlen=window_size)
        self.ema = None

    def apply(self, new_data):
        """
        Apply the selected smoothing method to the new data.

        Parameters:
            new_data (float): The new data point.

        Returns:
            float: The smoothed data point.
        """
        if self.method == 'none':
            return new_data
        elif self.method == 'moving_average':
            return self.moving_average(new_data)
        elif self.method == 'exponential_moving_average':
            return self.exponential_moving_average(new_data)
        else:
            raise ValueError(f"Invalid smoothing method: {self.method}")

    def moving_average(self, new_data):
        """
        Apply moving average smoothing.

        Parameters:
            new_data (float): The new data point.

        Returns:
            float: The smoothed data point.
        """
        self.data.append(new_data)
        return sum(self.data) / len(self.data)

    def exponential_moving_average(self, new_data):
        """
        Apply exponential moving average smoothing.

        Parameters:
            new_data (float): The new data point.

        Returns:
            float: The smoothed data point.
        """
        if self.ema is None:
            self.ema = new_data
        else:
            self.ema = (1 - self.alpha) * self.ema + self.alpha * new_data
        return self.ema



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

