from collections import namedtuple, UserDict
import ctypes
from functools import lru_cache, partial
import enum

import asyncio
import os
import json
import multiprocessing
from multiprocessing.connection import wait
from multiprocessing.queues import Queue as BaseQueue
from multiprocessing.managers import BaseManager
import time
import yaml
import queue
import threading
import uuid

from numbers import Real
from typing import List, Tuple

from cobs import cobs
from runtime.buffer import SharedMemoryBuffer
from runtime.util import read_conf_file, RuntimeException


Parameter = namedtuple('Parameter',
                       ['name', 'type', 'lower', 'upper', 'read', 'write'],
                       defaults=[float('-inf'), float('inf'), True, False])


class DeviceStructure(ctypes.Structure):
    """
    A struct representing a device (for example, a Smart Sensor).

    Example:

        >>> YogiBear = DeviceStructure.make_device_type('YogiBear',
        ...     [Parameter('duty_cycle', ctypes.c_float, -1, 1)])
        >>> motor = multiprocessing.Value(YogiBear, lock=False)
        >>> start = time.time()
        >>> motor.duty_cycle = -0.9
        >>> motor.last_modified('duty_cycle') - start < 0.1  # Updated recently?
        True
        >>> motor.duty_cycle = -1.1
        Traceback (most recent call last):
          ...
        ValueError: Assigned invalid value -1.1 to "YogiBear.duty_cycle" (not in bounds).
    """
    TIMESTAMP_SUFFIX = '_ts'

    @staticmethod
    def _get_timestamp_name(param_name: str):
        return param_name + DeviceStructure.TIMESTAMP_SUFFIX

    def last_modified(self, param_name: str) -> float:
        return getattr(self, DeviceStructure._get_timestamp_name(param_name))

    def __setattr__(self, param_name: str, value):
        """ Validate and assign the parameter's value, and update its timestamp. """
        if isinstance(value, Real):
            param = self._params[param_name]
            if not param.lower <= value <= param.upper:
                cls_name = self.__class__.__name__
                raise ValueError(f'Assigned invalid value {value} to '
                                 f'"{cls_name}.{param_name}" (not in bounds).')
        super().__setattr__(DeviceStructure._get_timestamp_name(param_name), time.time())
        super().__setattr__(param_name, value)

    def __getitem__(self, param_id):
        return self.__class__._params_by_id[param_id]

    @staticmethod
    def make_device_type(dev_name: str, params: List[Parameter]) -> type:
        """ Produce a named struct type. """
        fields = {}
        for param in params:
            fields[param.name] = param.type
            timestamp_name = DeviceStructure._get_timestamp_name(param.name)
            fields[timestamp_name] = ctypes.c_double
        return type(dev_name, (DeviceStructure,), {
            '_fields_': list(fields.items()),
            '_params': {param.name: param for param in params},
            '_params_by_id': params
        })

    @staticmethod
    def make_shared_device(device_type):
        name = device_type.__name__ + '-' + str(uuid.uuid4())
        buf = SharedMemoryBuffer(name, ctypes.sizeof(device_type))
        device = device_type.from_buffer(buf)
        device._buf = buf
        return device

    def __getstate__(self):
        device_type = type(self)
        return device_type.__name__, device_type._params_by_id, self._buf

    def __setstate__(self, state):
        pass


class SharedStoreRequest(enum.Enum):
    GET = enum.auto()
    SET = enum.auto()
    DEL = enum.auto()


COBS_DELIMETER = '\x00'


class SharedStoreServer(UserDict):
    def __init__(self, addr, data=None, name=None, daemon=True):
        self.addr, self.name, self.daemon = addr, name, daemon
        self.ready = threading.Event()
        super().__init__(data or {})

    def start(self):
        self.thread = threading.Thread(name=self.name, daemon=self.daemon,
                                       target=self.bootstrap_thread)
        self.thread.start()
        self.ready.wait()

    def bootstrap_thread(self):
        try:
            return asyncio.run(self.start_server())
        except asyncio.CancelledError:
            return

    async def start_server(self):
        self.server = await asyncio.start_unix_server(self.handle, self.addr)
        self.ready.set()
        async with self.server:
            await self.server.serve_forever()

    async def read(self, reader, buf):
        pass

    async def write(self, writer, buf):
        pass

    async def handle(self, reader, writer):
        loop = self.server.get_loop()
        # done, pending = await asyncio.wait(, loop=loop, return_when=asyncio.FIRST_COMPLETED)
        """
        print('Created!')
        while True:
            try:
                packet = await reader.readuntil(COBS_DELIMETER)
                decoded_data = cobs.decode(packet[:-len(COBS_DELIMETER)])
                print(decoded_data)
                await writer.drain()
            except pickle.PickleError:
                writer.write(cobs.encode(pickle.dumps()))
                writer.write(COBS_DELIMETER)
            except asyncio.IncompleteReadError:
                break
        """

    def stop(self):
        self.ready.wait()
        if self.server.is_serving():
            self.server.close()
            asyncio.run_coroutine_threadsafe(self.server.wait_closed(),
                                             self.server.get_loop())
            self.thread.join()
            self.ready.clear()


class SharedStoreClient(UserDict):
    def __init__(self, addr):
        self.addr = addr
        self.loop = asyncio.new_event_loop()
        open_coro = asyncio.open_unix_connection(self.addr)
        self.reader, self.writer = self.loop.run_until_complete(open_coro)
        super().__init__()

    def close(self):
        if not self.writer.is_closing() and not self.loop.is_closed():
            self.writer.close()
            self.loop.run_until_complete(self.writer.wait_closed())
            self.loop.close()
        else:
            raise RuntimeException('Cannot close client more than once.')

    def __getitem__(self, key):
        pass


server = SharedStoreServer('./test')
server.start()
client = SharedStoreClient('./test')
import time
time.sleep(3)
client.close()
server.stop()


"""
import time, random
async def target(addr, wait):
    # for _ in range(3):
    reader, writer = await asyncio.open_unix_connection(addr)
    await asyncio.sleep(2)
    writer.write(cobs.encode(b'\x00\x01') + b'\x00')
    await asyncio.sleep(wait)
    writer.write(cobs.encode(b'\x01') + b'\x00')
    writer.close()
    await writer.wait_closed()
    print('Closed client')
bus = MessageBus()
print('Bus initialized!')
child1 = multiprocessing.Process(target=lambda addr: asyncio.run(target(addr, 2)), args=(bus.addr,))
child1.start()
child2 = multiprocessing.Process(target=lambda addr: asyncio.run(target(addr, 1)), args=(bus.addr,))
child2.start()
child1.join()
child2.join()
bus.close()
# help(bus.server)
"""



"""
class StateManager(SharedStore):
    DEVICES_KEY = ''

    def __init__(self, schema):
        for protocol, devices in schema.items():
            for device_name, device in devices.items():
                pass

    @classmethod
    def load_from_schema(cls, filename: str):
        schema = read_conf_file(filename)
        return StateManager()
"""
