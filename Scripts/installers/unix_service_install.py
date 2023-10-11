import getpass
import os
import platform
import subprocess
import sys


def exit_on_error(reason: str = None):
    """
    Exit the program on error.

    Parameters:
        reason (str): The reason for the error. If not provided, it defaults to 'Unknown error.'

    Returns:
        None

    Raises:
        SystemExit: Always raises a SystemExit exception with exit code 1.
    """
    if not reason:
        reason = 'Unknown error.'
    sys.stderr.write(f'ERROR: {reason} | Exiting.\n')
    sys.exit(1)


def exit_if_root():
    """
    Check if the current user is running the script as root and exit if true.

    This function checks the effective user ID (`os.geteuid()`) to determine if the script is being run as root. If the user ID is 0, which is the root user, the function calls `exit_on_error()` with the error message "This script should not be run as root." This ensures that the script is not accidentally executed with root privileges, as it may have unintended consequences.

    Parameters:
    None

    Returns:
    None
    """
    if os.geteuid() == 0:
        exit_on_error('This script should not be run as root.')


def exit_if_windows():
    """
    Check if the current operating system is Windows and exit with an error message if it is.
    """
    if platform.system() == 'Windows':
        exit_on_error('This script should not be run on Windows.')


def setup_systemd_service():
    if platform.system() == "Linux" and os.path.exists("/etc/systemd/system"):
        current_user = getpass.getuser()
        service_content = f"""[Unit]
Description=Sense MQTT Broadcast Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 {os.path.abspath(__file__)}
WorkingDirectory={os.path.dirname(os.path.abspath(__file__))}
Restart=always
User={current_user}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

        service_file_path = "/etc/systemd/system/sense-mqtt-broadcast.service"

        # Note: 'sudo' is invoked here, so the user will be prompted for the admin password
        with open(service_file_path, "w") as f:
            f.write(service_content)

        subprocess.run(["sudo", "systemctl", "daemon-reload"])
        subprocess.run(["sudo", "systemctl", "enable", "sense-mqtt-broadcast.service"])
        subprocess.run(["sudo", "systemctl", "start", "sense-mqtt-broadcast.service"])
    elif platform.system() == 'Windows':
        exit_if_windows()


if __name__ == "__main__":
    exit_if_windows()
    exit_if_root()

    # Then, at the end or the beginning, call the setup function
    setup_systemd_service()
