import asyncio
from collections import UserDict
import enum
import glob
import multiprocessing
import os
import pickle
import re
import threading
import time
from functools import lru_cache
from runtime.util import AsyncioThread

from filelock import FileLock
import pynng
from pynng import Bus0 as Bus


class SharedStore(UserDict):
    """
    A shared inter-process key-value store.

    Supports the context management protocol.
    """
    class Command(enum.Flag):
        SET = enum.auto()
        DEL = enum.auto()
        MUTATE = SET | DEL

    ipc_name_format = '/tmp/runtime-store-{pid}.ipc'
    lock_name = '/tmp/runtime-store.lock'

    @staticmethod
    def get_transport(name):
        return 'ipc://' + name

    def get_bus_name(self, pid=None):
        pid = pid or os.getpid()
        return self.ipc_name_format.format(pid=pid)

    def get_bus_url(self, pid=None):
        return self.get_transport(self.get_bus_name(pid=pid))

    def get_peers(self):
        return glob.glob(self.get_bus_name('*'))

    def __init__(self, name: str = None):
        self.name, self.ready, self.bus = name, threading.Event(), Bus()
        super().__init__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.stop()

    def start(self):
        self.thread = AsyncioThread(name=self.name, daemon=True,
                                    target=self.bootstrap_bus_listener)
        self.thread.start()

    def stop(self):
        if hasattr(self, 'thread'):
            self.thread.stop()
            self.thread.join()
        self.bus.close()

    async def bootstrap_bus_listener(self):
        with self.bus:
            with FileLock(self.lock_name):
                for peer in self.get_peers():
                    try:
                        self.bus.dial(self.get_transport(peer), block=True)
                    except pynng.exceptions.ConnectionRefused:
                        pass  # TODO: raise warning
                self.bus.listen(self.get_bus_url())
            await self.recv_from_bus()

    async def recv_from_bus(self):
        while True:
            command, key, *data = pickle.loads(await self.bus.arecv())
            if command is SharedStore.Command.SET:
                super().__setitem__(key, data[0])
            elif command is SharedStore.Command.DEL:
                super().__delitem__(key)
            else:
                pass  # Raise warning

    def send_command(self, command, *data):
        self.bus.send(pickle.dumps((command, ) + data))

    def __setitem__(self, key, value):
        self.send_command(SharedStore.Command.SET, key, value)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.send_command(SharedStore.Command.DEL, key)
        super().__delitem__(key)


async def _target(whoami):
    with SharedStore() as sm:
        await asyncio.sleep(2)
        sm[whoami] = whoami
    print('Done!')


def target(whoami):
    asyncio.run(_target(whoami))


if __name__ == '__main__':
    children = [
        multiprocessing.Process(target=target, args=(i, ))
        for i in range(3)
    ]
    for child in children:
        child.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        for child in children:
            child.terminate()
            child.join()
