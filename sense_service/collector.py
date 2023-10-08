from threading import Thread
import time


class HighResTempCollector:
    """
    Class to continuously collect high-resolution temperature data from the Sense HAT.

    Usage Example:
        >>> temp_collector = HighResTempCollector(sense, smoother, interval=1)
        >>> temp_collector.start()
    """
    
    def __init__(self, sense, smoother, interval=1):
        """
        Initialize the HighResTempCollector class.

        Parameters:
            sense (SenseHat): An instance of the SenseHat class.
            smoother (SensorDataSmoother): An instance of the SensorDataSmoother class.
            interval (int): Time interval in seconds between each data collection.
        """
        self.sense = sense
        self.smoother = smoother
        self.interval = interval
        self.running = False

    def collect(self):
        """Continuously collect sensor data at high resolution."""
        self.running = True
        while self.running:
            raw_temp = self.sense.get_temperature()
            if self.smoother:
                self.smoother.apply(raw_temp)
            time.sleep(self.interval)

    def start(self):
        """Start the high-resolution data collection in a new thread."""
        self.thread = Thread(target=self.collect, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the high-resolution data collection."""
        self.running = False
        self.thread.join()
