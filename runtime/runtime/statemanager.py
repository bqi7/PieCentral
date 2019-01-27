from collections import namedtuple, UserDict
import ctypes
from functools import lru_cache, partial
import enum

import abc
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
import pickle

from numbers import Real
from typing import List, Tuple

from cobs import cobs
from runtime.buffer import SharedMemoryBuffer, BinaryRingBuffer
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


class SharedStore(UserDict, abc.ABC):
    class Command(enum.Enum):
        SET = enum.auto()
        DEL = enum.auto()

    delimeter = b'\x00'

    def __init__(self, addr, data=None, name=None, daemon=True):
        self.addr, self.name, self.daemon = addr, name, daemon
        super().__init__(data or {})

    def start(self):
        self.thread = threading.Thread(name=self.name, daemon=self.daemon,
                                       target=self.bootstrap_thread)
        self.thread.start()

    @abc.abstractmethod
    async def main(self):
        pass

    def bootstrap_thread(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.main_task = self.loop.create_task(self.main())
            self.loop.run_until_complete(self.main_task)
        except asyncio.CancelledError:
            pass
        finally:
            tasks = asyncio.all_tasks(self.loop)
            for task in tasks:
                if not task.cancelled():
                    self.loop.call_soon_threadsafe(task.cancel)
            tasks = asyncio.gather(*tasks, return_exceptions=True)
            self.loop.run_until_complete(tasks)
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.stop()
            self.loop.close()

    def stop(self):
        if hasattr(self, 'main_task') and not self.main_task.cancelled():
            self.loop.call_soon_threadsafe(self.main_task.cancel)
        if hasattr(self, 'thread'):
            self.thread.join()

    async def cobs_write(self, writer, data):
        packet = cobs.encode(pickle.dumps(data))
        writer.write(packet)
        writer.write(self.delimeter)
        await writer.drain()

    async def cobs_read(self, reader):
        packet = await reader.readuntil(self.delimeter)
        return pickle.loads(cobs.decode(packet[:-len(self.delimeter)]))

    async def recv_update(self, reader):
        command, key, *value = data = await self.cobs_read(reader)
        if command is SharedStore.Command.SET:
            super().__setitem__(key, value[0])
        elif command is SharedStore.Command.DEL:
            super().__delitem__(key)
        return data


class SharedStoreServer(SharedStore):
    def __init__(self, *args, buf_max_size=1024, **kwargs):
        self.ready = threading.Event()
        self.buf_lock, self.buf_max_size = asyncio.Lock(), buf_max_size
        self.update_buffers = {}
        super().__init__(*args, **kwargs)

    def start(self):
        super().start()
        self.ready.wait()

    async def main(self):
        self.server = await asyncio.start_unix_server(self.handle, self.addr)
        async with self.server:
            self.ready.set()
            await self.server.serve_forever()

    def stop(self):
        self.ready.wait()
        if self.server.is_serving():
            try:
                self.server.close()
            except TypeError:  # HACK
                pass
        self.ready.clear()
        super().stop()

    async def read(self, reader, key):
        while True:
            try:
                data = await self.recv_update(reader)
                async with self.buf_lock:
                    for update_key, buf in self.update_buffers.items():
                        if update_key != key:
                            await buf.put(data)
            except pickle.PickleError:
                continue

    async def write(self, writer, key):
        buf = self.update_buffers[key]
        while True:
            try:
                await self.cobs_write(writer, await buf.get())
            except pickle.PickleError:
                continue

    async def handle(self, reader, writer):
        try:
            key = str(uuid.uuid4())
            async with self.buf_lock:
                self.update_buffers[key] = asyncio.Queue(maxsize=self.buf_max_size)

            tasks = {self.read(reader, key), self.write(writer, key)}
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            for task in pending:
                task.cancel()
        finally:
            writer.close()
            async with self.buf_lock:
                if key in self.update_buffers:
                    del self.update_buffers[key]

    async def send_set(self, key, value):
        async with self.buf_lock:
            for update_key, buf in self.update_buffers.items():
                await buf.put((SharedStore.Command.SET, key, value))

    async def send_del(self, key):
        async with self.buf_lock:
            for update_key, buf in self.update_buffers.items():
                await buf.put((SharedStore.Command.DEL, key))

    def __setitem__(self, key, value):
        asyncio.run_coroutine_threadsafe(self.send_set(key, value), self.loop)
        return super().__setitem__(key, value)

    def __delitem__(self, key, value):
        asyncio.run_coroutine_threadsafe(self.send_del(key), self.loop)
        return super().__delitem__(key)


class SharedStoreClient(SharedStore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def main(self):
        try:
            reader, self.writer = await asyncio.open_unix_connection(self.addr)
            while True:
                try:
                    await self.recv_update(reader)
                except pickle.PickleError:
                    continue
        finally:
            self.writer.close()

    def __setitem__(self, key, value):
        task = self.cobs_write(self.writer, (SharedStore.Command.SET, key, value))
        asyncio.run_coroutine_threadsafe(task, self.loop)
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        task = self.cobs_write(self.writer, (SharedStore.Command.DEL, key))
        asyncio.run_coroutine_threadsafe(task, self.loop)
        return super().__delitem__(key)


import time
server = SharedStoreServer('./test')
server.start()
client = SharedStoreClient('./test')
client.start()
time.sleep(0.05)
server['x'] = 1
time.sleep(0.05)
print(client['x'])
client['x'] = 2
time.sleep(0.05)
print(server['x'])
del client['x']
time.sleep(0.1)
assert 'x' not in server
client.stop()
server.stop()



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
