"""
Contains custom exceptions for SenseService
"""


class InvalidTemperatureSourceError(Exception):
    message = 'Invalid value for "temperature_source" must be one of; "pressure", or "humidity"!'
    def __init__(self, *args, **kwargs):
        super().__init__(self.message)

