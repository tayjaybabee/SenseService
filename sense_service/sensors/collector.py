from __future__ import annotations

from threading import Thread
from typing import Optional
import time


class HighResTempCollector:
    """
    Class to continuously collect high-resolution temperature data from the Sense HAT.

    This class is intended to be instantiated by the SenseHatMQTT class,
    which will pass itself as the 'sense' parameter.

    Usage Example:
        >>> # Assume 'sense' and 'smoother' are provided by the SenseHatMQTT class
        >>> # and SensorDataSmoother class, respectively.
        >>> sense = ...
        >>> smoother = ...
        >>> temp_collector = HighResTempCollector(sense, smoother, interval=1)
        >>> temp_collector.start()
    """
    from sense_service import SenseHatMQTT, SensorDataSmoother

    def __init__(
            self,
            sense: 'SenseHatMQTT',
            smoother: 'SensorDataSmoother',
            interval: (int | float) = None,
            high_res_interval: (int | float) = None) -> None:
        """
        Initialize the HighResTempCollector class.

        Parameters:
            sense (SenseHat): An instance of the SenseHat class.
            smoother (SensorDataSmoother): An instance of the SensorDataSmoother class.
            interval (int): Time interval in seconds between each data collection.
        """
        used_interval_aliases = [_ for _ in [interval, high_res_interval] if _ is not None]
        self.sense = sense
        self.smoother = smoother

        if len(used_interval_aliases) > 1:
            raise ValueError("Only one of 'interval' and 'high_res_interval' can be specified!")

        self.interval = interval or high_res_interval

        self.running = False
        self.thread: Optional[Thread] = None

    def collect(self) -> None:
        """Continuously collect sensor data at high resolution."""
        self.running = True
        while self.running:
            try:
                raw_temp = self.sense.get_temperature()
                if self.smoother:
                    self.smoother.apply(raw_temp)
            except Exception as e:
                print(f"Error in data collection: {e}")
            time.sleep(self.interval)

    def start(self) -> None:
        """Start the high-resolution data collection in a new thread."""
        self.thread = Thread(target=self.collect, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the high-resolution data collection."""
        self.running = False
        if self.thread:
            self.thread.join()

    def __del__(self) -> None:
        """Ensure the collection thread is stopped upon object destruction."""
        self.stop()
