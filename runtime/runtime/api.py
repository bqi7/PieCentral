import io


class Actions:
    @staticmethod
    async def sleep(seconds: float):
        await asyncio.sleep(seconds)


class Gamepad:
    pass


class Robot:
    def __init__(self, log_file: str):
        self.log_file = log_file
