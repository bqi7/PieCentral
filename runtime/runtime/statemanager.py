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

from posix_ipc import Semaphore
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
        self.join_lock = Semaphore('/runtime-join')
        self.mutate_lock = Semaphore('/runtime-mutate')
        self.thread = AsyncioThread(name=self.name, daemon=True,
                                    target=self.bootstrap_bus_listener)
        self.thread.start()

    def stop(self):
        self.ready.wait()
        self.thread.stop()
        self.thread.join()
        self.ready.clear()
        self.bus.close()
        self.join_lock.close()
        self.mutate_lock.close()

    async def bootstrap_bus_listener(self):
        with self.bus:
            # This section executes atomically to ensure the network is
            # strongly connected.
            with self.:
                for peer in self.get_peers():
                    try:
                        self.bus.dial(self.get_transport(peer), block=True)
                    except (pynng.exceptions.ConnectionRefused, pynng.exceptions.Closed):
                        pass  # TODO: raise warning
                self.bus.listen(self.get_bus_url())
            self.ready.set()
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
        self.ready.wait()
        self.bus.send(pickle.dumps((command, ) + data))

    def __setitem__(self, key, value):
        # with FileLock(self.mutate_lock_name):
        self.send_command(SharedStore.Command.SET, key, value)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        # with FileLock(self.mutate_lock_name):
        self.send_command(SharedStore.Command.DEL, key)
        super().__delitem__(key)
