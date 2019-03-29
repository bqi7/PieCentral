import abc


class Monitor(UserDict, abc.ABC):
    """
    A monitor for managing resources.
    """
    def __init__(self):
        self.resources = {}

    @abc.abstractmethod
    async def monitor_resource(self, name: str):
        pass

    @abc.abstractmethod
    async def spin(self):
        pass

    @abc.abstractmethod
    def terminate(self, timeout=None):
        pass


class ServerMonitor(Monitor):
    pass


class DeviceMonitor(Monitor):
    pass
