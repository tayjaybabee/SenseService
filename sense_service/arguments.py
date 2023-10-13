from __future__ import annotations

from argparse import ArgumentParser, Namespace
from sense_service.environment import Environment
from sense_service.__about__ import __PROG__ as PROG_NAME
from sense_service.sensors import VALID_TEMPERATURE_UNITS, VALID_TEMPERATURE_SOURCES, VALID_SMOOTHING_ALGORITHMS


class Arguments(ArgumentParser):
    def __init__(self, *args, **kwargs):
        self.env_vars = Environment()
        super().__init__(*args, **kwargs)

        self.prog = PROG_NAME
        self.description = 'Sense Service for Raspberry Pi'

        self.add_argument(
            '-u', '--unit',
            action='store',
            default='C',
            help='The unit temperature should be read in.',
            choices=[unit[0] for unit in VALID_TEMPERATURE_UNITS],
        )

        self.add_argument(
            '--hat-version',
            action='store',
            default='2',
            help='The version of the Sense HAT to use. (Note: this just hides a warning about a color sensor if you '
                 'indicate that you have the first SenseHat)',
            required=False,
            choices=['1', '2'],
        )

        self.add_argument(
            '--high-res-interval',
            action='store',
            default='1.5',
            help='High resolution interval in seconds.',
            required=False,
        )

        self.add_argument(
            '--temp-source',
            action='store',
            default='humidity',
            help='Which sensor should the program take temperature readings from.',
            choices=VALID_TEMPERATURE_SOURCES,
            required=False,
        )

        self.add_argument(
            '--smoothing-algorithm',
            action='store',
            default='moving_average',
            choices=VALID_SMOOTHING_ALGORITHMS,
            help='The smoothing algorithm to use.',
            required=False,
        )

        self.add_argument(
            '--broadcast-interval',
            action='store',
            default='3',
            help='The interval between publishing sensor data.',
            required=False
        )

        self.add_argument(
            '--display-real-feel',
            action='store_true',
            default=False,
            help='Display the real feel temperature on the SenseHat\'s 8x8 LED matrix.',
        )

        self.add_argument(
            '--broker-address',
            action='store',
            default='localhost',
            help='The address of the MQTT broker service you wish to publish to.',
            required=False
        )

        self.add_argument(
            '--broker-port',
            action='store',
            default='1883',
            help='The port of the MQTT broker service you wish to publish to.',
            required=False
        )

        self.add_argument(
            '--topic',
            action='store',
            default='rpi-sense',
            help='The MQTT topic you wish to publish to.',
            required=False
        )

        self.__parsed = None

    @property
    def args(self) -> (Namespace | None):
        if not self.__parsed:
            self.__parsed = self.parse_args()

        return self.parse_args()

    def parse_args(self, *args, **kwargs) -> Namespace:
        """
        Parses the arguments passed to the function.

        Args:
            *args: Positional arguments passed to the function.
            **kwargs: Keyword arguments passed to the function.

        Returns:
            The result of calling the `parse_args` method of the superclass.
        """
        return super().parse_args(*args, **kwargs)

ARGUMENTS = Arguments()
PARSED = ARGUMENTS.args
import sys

print(sys.argv)
