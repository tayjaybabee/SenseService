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


class Temperature:
    """Manages temperature conversions and calculations."""

    @staticmethod
    def convert_c_to_f(temp):
        """Convert a temperature in Celsius to Fahrenheit."""
        return (temp * 1.8) + 32

    @staticmethod
    def convert_c_to_k(temp):
        """Convert a temperature in Celsius to Kelvin."""
        return temp + 273.15

    @staticmethod
    def calculate_dew_point(temp, humidity, unit='C'):
        """
        Calculate dew point based on temperature and humidity.

        Parameters:
            temp (float): Temperature.
            humidity (float): Relative humidity.
            unit (str): Unit of the temperature ('C', 'F', 'K').

        Returns:
            float: Dew point temperature in the same unit as input.
        """

        # Convert temperature to Celsius for dew point calculation
        if unit == 'F':
            temp = (temp - 32) / 1.8
        elif unit == 'K':
            temp = temp - 273.15

        # Calculate dew point in Celsius
        dew_point_c = temp - ((100 - humidity) / 5)

        # Convert dew point back to the original unit
        if unit == 'F':
            return (dew_point_c * 1.8) + 32
        elif unit == 'K':
            return dew_point_c + 273.15
        return dew_point_c

    @staticmethod
    def calculate_heat_index(temp, humidity, unit='C'):
        """Calculate heat index based on temperature and humidity."""
        # Convert temperature to Celsius for heat index calculation
        if unit == 'F':
            temp = (temp - 32) / 1.8
        elif unit == 'K':
            temp = temp - 273.15

        # Calculate heat index in Celsius
        heat_index_c = temp if temp < 27 else (
                -8.78469475556 + 1.61139411 * temp + 2.33854883889 * humidity
                - 0.14611605 * temp * humidity - 0.012308094 * temp ** 2
                - 0.0164248277778 * humidity ** 2 + 0.002211732 * temp ** 2 * humidity
                + 0.00072546 * temp * humidity ** 2 - 0.000003582 * temp ** 2 * humidity ** 2
        )

        # Convert heat index back to the original unit
        if unit == 'F':
            return (heat_index_c * 1.8) + 32
        elif unit == 'K':
            return heat_index_c + 273.15
        return heat_index_c
