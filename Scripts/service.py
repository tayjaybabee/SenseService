import os
import platform
import sys
import time


def daemonize():
    """
    Convert the current process to a daemon.

    This method is cross-platform, supporting both UNIX and Windows systems.

    Usage Example:
    --------------

    >>> daemonize()
    """
    if platform.system() == 'Windows':
        import win32api, win32process

        # Create a new process to make it independent
        hProcess = win32api.GetCurrentProcess()
        dwProcessId = win32process.GetProcessId(hProcess)
        new_process = win32api.ShellExecute(
            0, "open", sys.executable, f"{__file__} {dwProcessId}", None, 0
        )
    else:
        # Fork a child process
        try:
            pid = os.fork()
        except OSError as e:
            sys.exit(f"Failed to fork child process: {e}")

        # Exit from the parent process
        if pid > 0:
            sys.exit(0)

        # Become the leader of a new session and detach from terminal
        os.setsid()


def main():
    """
    Main function where the daemon-specific code resides.

    Usage Example:
    ---------------

    >>> main()
    """
    while True:
        # Your code goes here
        print("Daemon is running.")
        time.sleep(5)


if __name__ == "__main__":
    daemonize()
    main()
