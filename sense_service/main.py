from atexit import register
import paho.mqtt.client as mqtt
import json
import time
from os import environ

from threading import Thread, Lock

from .errors import InvalidTemperatureSourceError
from .helpers import SuppressLogging, logging, SensorDataSmoother
from .collector import HighResTempCollector


class Environment:
    """Manages environment variables for temperature unit and HAT mode."""

    def __init__(self):
        self.TEMP_UNIT = self.get_temp_unit()
        self.NO_HAT_MODE = self.get_no_hat_mode()
        self.HAT_VER = self.get_hat_version()
        self.current_display_thread = None

    @staticmethod
    def get_temp_unit():
        """Get temperature unit from environment variable."""
        temp_unit = environ.get('TEMP_UNIT', 'C').lower()
        return 'F' if temp_unit in ['fahrenheit', 'f'] else 'K' if temp_unit in ['kelvin', 'k'] else 'C'

    @staticmethod
    def get_no_hat_mode():
        """Get NO HAT mode from environment variable."""
        return environ.get('NOHAT', 'false').lower() in ['true', '1']

    @staticmethod
    def get_hat_version():
        """Get HAT version from environment variable."""
        return environ.get('HAT_VER', '2')


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


class SenseHatMQTT:
    """A class to read data from a Sense HAT and send it to an MQTT broker."""
    VALID_TEMP_SOURCES = [
        'humidity',
        'pressure'
        ]

    def __init__(self, broker_address, data_smoother=None, high_res_interval=1, temp_source=None):
        """
        Initialize the SenseHatMQTT class.

        Parameters:
            broker_address (str): The address of the MQTT broker.
            data_smoother (SensorDataSmoother, optional): An instance of the SensorDataSmoother class.

        Usage Example:
            >>> sense_mqtt = SenseHatMQTT("broker_address_here")
        """
        self.running = False
        self.data_smoother = data_smoother

        # Create a new MQTT client instance and set its name to "SenseHat"
        self.client = mqtt.Client("SenseHat")

        # Assign event handlers for MQTT client's on_connect and on_message events
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.__temp_source = None
        
        # Set the source sensor for the temperature readings
        if temp_source is not None:
            self.temperature_source = temp_source
        else:
            self.temperature_source = 'humidity'
            

        # Instantiate the Environment class to manage environment variables
        env = Environment()

        # Store the temperature unit from the Environment instance
        self.TEMP_UNIT = env.TEMP_UNIT

        # Import SenseHat or SenseEmu based on NO_HAT_MODE environment variable
        if not env.NO_HAT_MODE:
            from sense_hat import SenseHat
        else:
            from sense_emu import SenseHat

        # Store the HAT version from the Environment instance
        self.HAT_VER = env.HAT_VER

        # Suppress logging if the HAT version is '1', then instantiate SenseHat.
        # NOTE:
        #     First revision SenseHATs do not have a color sensor and therefore always throw a 'WARNING' log entry that
        #     just clutters output and confuses, and serves no use. So, we suppress that log entry.
        if self.HAT_VER == '1':
            with SuppressLogging('root', logging.WARNING):
                self.sense = SenseHat()
        else:
            # If the HAT is revision 2 we instantiate without suppressing warnings
            self.sense = SenseHat()

        # Connect to the MQTT broker on the specified address and default port (1883)
        self.client.connect(broker_address, 1883, 60)

        # Create and start the high-resolution temperature collector
        self.temp_collector = HighResTempCollector(self.sense, self.data_smoother, high_res_interval)
        self.temp_collector.start()

        # Initialize a Lock object to synchronize display access among threads
        self.display_lock = Lock()
        
    @property
    def temperature_source(self):
        return self.__temp_source
    
    @temperature_source.setter
    def temperature_source(self, new):
        if new.lower() not in self.VALID_TEMP_SOURCES:
            raise InvalidTemperatureSourceError()
        
        self.__temp_source = new.lower()

    def on_connect(self, client, userdata, flags, rc):
        """Called when the client receives a CONNACK response from the server."""
        print(f"Connected with result code {rc}")

    def on_message(self, client, userdata, msg):
        """Called when a message has been received on a topic that the client subscribes to."""
        print(msg.topic + " " + str(msg.payload))

    def get_temp(self):
        """Get the temperature from the Sense HAT."""
        
        if self.temperature_source == 'humidity':
            raw_temp = self.sense.get_temperature_from_humidity()
        elif self.temperature_source == 'pressure':
            raw_temp = self.sense.get_temperature_from_pressure()

        # Apply smoothing
        if self.data_smoother:
            temp = self.data_smoother.apply(raw_temp)
        else:
            temp = raw_temp

        if self.TEMP_UNIT == 'F':
            temp = Temperature.convert_c_to_f(temp)
        elif self.TEMP_UNIT == 'K':
            temp = Temperature.convert_c_to_k(temp)

        return temp
    
    def publish_sense_data(self, payload):
        """Publishes Sense HAT data to MQTT broker."""

        self.client.publish("rpi-sense", json.dumps(payload))

    def get_sense_data(self):
        """
        Collects data from the Sense HAT and calculates additional metrics like real-feel and dew point.

        Returns:
            dict: Sensor data including temperature, pressure, humidity, real-feel, and dew point.
        """

        temp = self.get_temp()
        pressure = self.sense.get_pressure()
        humidity = self.sense.get_humidity()
        heat_index = Temperature.calculate_heat_index(temp, humidity, self.TEMP_UNIT)
        dew_point = Temperature.calculate_dew_point(temp, humidity, self.TEMP_UNIT)

        return {
            "temperature": round(temp, 2),
            "pressure": round(pressure, 2),
            "humidity": round(humidity, 2),
            "real_feel": round(heat_index, 2),
            "dew_point": round(dew_point, 2)
        }

    def display_real_feel(self, data):
        with self.display_lock:
            self.sense.show_message(f"Real Feel: {data['real_feel']:0.2f}", scroll_speed=0.05)

            time.sleep(3)

    def stop(self):
        """Stop the MQTT client loop."""
        self.client.loop_stop()
        self.temp_collector.stop()
        self.running = False
        time.sleep(3)
        self.sense.clear()

    def display_worker(self):
        while self.running:
            self.display_real_feel(self.get_sense_data())
            self.sense.clear()
            time.sleep(3)
            if not self.running:
                break
        self.display_thread = None
        print('Worker stopped')

    def run(self, display=False):
        """Run the MQTT client loop and publish Sense HAT data."""
        self.client.loop_start()
        self.running = True

        if display:
            display_thread = Thread(target=self.display_worker, daemon=True)
            display_thread.start()
            self.display_thread = display_thread

        try:
            while self.running:
                data = self.get_sense_data()
                self.publish_sense_data(data)

                time.sleep(3)
        except KeyboardInterrupt:
            self.stop()

if __name__ == "__main__":
    sense_mqtt = SenseHatMQTT("ds9.local")
    register(sense_mqtt.stop)
    sense_mqtt.run(display=True)
