import os

import servicemanager
import win32event
import win32service
import win32serviceutil


class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'MyService'
    _svc_display_name_ = 'My Service'
    _svc_description_ = 'This is a description of My Service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        self.remove_pid_file()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.create_pid_file()
        self.main()

    def create_pid_file(self):
        pid = os.getpid()
        with open("MyService.pid", "w") as f:
            f.write(str(pid))

    def remove_pid_file(self):
        if os.path.exists("MyService.pid"):
            os.remove("MyService.pid")

    def main(self):
        # Your logic here
        from time import sleep
        while self.is_alive:
            # Your logic here, e.g., fetch data, run computations, etc.
            sleep(4)
            break
