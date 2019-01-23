import io


class ReadDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot read parameter "{param_name}" of sensor "{sensor_name}".')


class WriteDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot write parameter "{param_name}" of sensor "{sensor_name}".')


class Actions:
    @staticmethod
    async def sleep(seconds: float):
        await asyncio.sleep(seconds)


class Gamepad:
    pass


class Robot:
    def __init__(self, log_file: str):
        self.log_file = log_file
