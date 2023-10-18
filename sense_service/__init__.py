from __future__ import annotations

import json
import time
from threading import Thread, Lock
from typing import Dict, Optional

import paho.mqtt.client as mqtt

from sense_service.environment import Environment
from sense_service.errors import InvalidTemperatureSourceError
from sense_service.helpers import SuppressLogging, logging
from sense_service.sensors import SensorDataSmoother, Temperature


def on_connect(client, userdata, flags, rc):
    """Called when the client receives a CONNACK response from the server."""
    print(f"Connected with result code {rc}")
    print(f'Client ID: {client._client_id}')


def on_message(client, userdata, msg):
    """Called when a message has been received on a topic that the client subscribes to."""
    print(msg.topic + " " + str(msg.payload))


class SenseHatMQTT:
    """A class to read data from a Sense HAT and send it to an MQTT broker."""

    VALID_TEMP_SOURCES = ['humidity', 'pressure']

    def __init__(
            self,
            broker_address: str,
            broker_port: int,
            topic: Optional[str] = None,
            data_smoother: Optional[SensorDataSmoother] = None,
            high_res_interval: (int | float) = 1,
            temp_source: Optional[str] = None,
            temp_unit: Optional[str] = None,
            hat_version: Optional[str] = None
    ) -> None:
        """
        Initialize the SenseHatMQTT class.

        Parameters:
            broker_address (str): The address of the MQTT broker.
            broker_port (int): The port of the MQTT broker.
            topic (str, optional): The topic to publish sense data to, default is 'rpi-sense'.
            data_smoother (SensorDataSmoother, optional): An instance of the SensorDataSmoother class.
            high_res_interval (int): The interval for high-resolution temperature data collection.
            temp_source (str, optional): The source for temperature readings.

        Usage Example:
            >>> sense = SenseHatMQTT("broker_address_here")
        """
        self.running = False
        self.data_smoother = data_smoother

        # Create a new MQTT client instance and set its name to "SenseHat"
        self.client = mqtt.Client("SenseHat")

        # Assign event handlers for MQTT client's on_connect and on_message events
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        self.__temp_source = None

        # Set the source sensor for the temperature readings
        if temp_source is not None:
            self.temperature_source = temp_source
        else:
            self.temperature_source = 'humidity'

        # Instantiate the Environment class to manage environment variables
        env = Environment()

        # Store the temperature unit from the Environment instance
        self.TEMP_UNIT = temp_unit or env.get_temp_unit() or 'C'

        # Import SenseHat or SenseEmu based on NO_HAT_MODE environment variable
        if not env.NO_HAT_MODE:
            from sense_hat import SenseHat
        else:
            from sense_emu import SenseHat

        # Store the HAT version from the Environment instance
        self.HAT_VER = hat_version or env.get_hat_version() or '2'

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

        self.__topic = topic or 'rpi-sense'

        self.broker_address = broker_address
        self.broker_port = broker_port

        # Connect to the MQTT broker on the specified address and default port (1883)
        self.client.connect(self.broker_address, self.broker_port, 60)

        self.__temp_collector = None

        # Initialize a Lock object to synchronize display access among threads
        self.display_lock = Lock()

        # Initialize a pointer to a possible display thread
        self.__display_thread = None

        self.__high_res_interval = high_res_interval

    @property
    def display_thread(self):
        return self.__display_thread

    @display_thread.setter
    def display_thread(self, new: Thread):
        if not isinstance(new, Thread):
            raise TypeError('display_thread must be a Thread object!')

        self.__display_thread = new

    @display_thread.deleter
    def display_thread(self):
        self.__display_thread.join()
        self.__display_thread = None

    @property
    def high_res_interval(self):
        return self.__high_res_interval

    @property
    def temperature_source(self):
        return self.__temp_source

    @temperature_source.setter
    def temperature_source(self, new):
        if new.lower() not in self.VALID_TEMP_SOURCES:
            raise InvalidTemperatureSourceError()

        self.__temp_source = new.lower()

    @property
    def temp_collector(self):
        return self.__temp_collector

    @property
    def topic(self) -> str:
        """
        The topic to publish data to.

        Returns:
            str: The topic to publish data to.
        """
        return self.__topic

    @topic.setter
    def topic(self, new: str):
        if not isinstance(new, str):
            raise TypeError('topic must be a string!')

    def get_temp(self):
        """Get the temperature from the Sense HAT."""
        raw_temp = None

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

    def publish_sense_data(self, payload: Dict[str, float]) -> None:
        """Publishes Sense HAT data to MQTT broker."""
        try:
            self.client.publish(self.topic, json.dumps(payload))
        except Exception as e:  # You can specify more concrete exception types
            logging.error(f"Failed to publish data to MQTT broker: {e}")

    def get_sense_data(self) -> Dict[str, float]:
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
            self.sense.show_message(f'Real Feel: {data["real_feel"]:0.2f}', scroll_speed=0.05)

            time.sleep(3)

    def stop(self):
        """Stop the MQTT client loop."""
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

    def run(self, display: bool = False) -> None:
        """Run the MQTT client loop and publish Sense HAT data."""
        self.start_mqtt_loop()
        self.start_collector()
        self.start_display_thread_if_needed(display)
        self.publish_loop()

    def start_collector(self):
        from sense_service.sensors.collector import HighResTempCollector
        self.__temp_collector = HighResTempCollector(self, self.data_smoother, high_res_interval=self.high_res_interval)

    def start_mqtt_loop(self) -> None:
        self.client.loop_start()
        self.running = True

    def start_display_thread_if_needed(self, display: bool) -> None:
        if display:
            display_thread = Thread(target=self.display_worker, daemon=True)
            display_thread.start()
            self.display_thread = display_thread

    def publish_loop(self) -> None:
        try:
            while self.running:
                data = self.get_sense_data()
                self.publish_sense_data(data)
                time.sleep(3)
        except KeyboardInterrupt:
            del self

    def __del__(self) -> None:
        """Ensure all threads are stopped and resources are released."""
        self.stop()
