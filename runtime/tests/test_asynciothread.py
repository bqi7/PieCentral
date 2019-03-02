import asyncio
import unittest
import threading
import time
from runtime.util import AsyncioThread


class TestAsyncioThread(unittest.TestCase):
    name = 'asyncio-thread'

    def test_basic_start_join(self):
        ok = False
        async def target(self, x, y=1):
            # FIXME: using `self.assert*` methods don't seem to work here.
            nonlocal ok
            if x == 2 and y == 2:
                ok = True
        thread = AsyncioThread(name=self.name, target=target, args=(self, 2,),
                               kwargs={'y': 2})
        thread.start()
        thread.join()
        self.assertTrue(ok)

    def test_stop(self):
        ready = threading.Event()
        async def target():
            while True:
                await asyncio.sleep(1)
                ready.set()
        thread = AsyncioThread(name=self.name, target=target)
        thread.start()
        ready.wait()
        thread.stop()
        thread.join()


if __name__ == '__main__':
    unittest.main()
