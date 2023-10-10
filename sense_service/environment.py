from os import environ


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
