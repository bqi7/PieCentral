import io
from runtime.util import RuntimeBaseException


class ReadDisabledError(RuntimeBaseException):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot read parameter "{param_name}" of sensor "{sensor_name}".')


class WriteDisabledError(RuntimeBaseException):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot write parameter "{param_name}" of sensor "{sensor_name}".')


class Actions:
    @staticmethod
    async def sleep(seconds: float):
        await asyncio.sleep(seconds)


class Gamepad:
    pass


class Robot:
    pass
