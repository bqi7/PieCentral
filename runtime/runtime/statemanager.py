from collections import namedtuple, UserDict
import ctypes
from functools import lru_cache, partial
import enum

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

from runtime.messaging import SharedMemoryBuffer


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


# YogiBear = DeviceStructure.make_device_type('YogiBear',
#      [Parameter('duty_cycle', ctypes.c_float, -1, 1)])
# types = {'yogibear': }
# motor = DeviceStructure.make_shared_device(types['yogibear'])
# import pickle
# print(pickle.dumps(motor))
# motor2 = pickle.loads(pickle.dumps(motor))
# print(motor.duty_cycle, motor2.duty_cycle)
# motor2.duty_cycle = 0.5
# print(motor.duty_cycle, motor2.duty_cycle)



class MessageBusProcess(multiprocessing.Process):
    """
    A specialized process than can broadcast messages to all other processes on
    the bus.

    Example:

        >>> def target(done):
        ...     MessageBusProcess.broadcast('OK!')
        ...     done.set()
        >>> done = multiprocessing.Event()
        >>> child = MessageBusProcess(target=target, args=(done,))
        >>> child.start()
        >>> done.wait()
        True
        >>> MessageBusProcess.consume()
        'OK!'
        >>> child.join()
        >>> child.close()
    """
    def __init__(self, *args, forward=True, **kwargs):
        conn_to_parent, conn_to_child = multiprocessing.Pipe()
        parent = multiprocessing.current_process()
        if not hasattr(parent, '_connections'):
            parent._connections = {}
        terminated = multiprocessing.Event()
        parent._connections[conn_to_child] = terminated
        self._connections = {conn_to_parent: terminated}
        self._forward = forward
        super().__init__(*args, **kwargs)

    def close(self):
        for terminated in getattr(self, '_connections', {}).values():
            terminated.set()
        super().close()

    @staticmethod
    def get_connections():
        process = multiprocessing.current_process()
        connections = getattr(process, '_connections', {})
        process._connections = {
            conn: terminated for conn, terminated in connections.items()
            if not terminated.is_set()}
        yield from process._connections

    @staticmethod
    def broadcast(payload):
        for conn in MessageBusProcess.get_connections():
            conn.send(payload)

    @staticmethod
    def consume(timeout=None):
        process = multiprocessing.current_process()
        connections = list(MessageBusProcess.get_connections())
        while connections:
            try:
                ready_connections = wait(connections, timeout)
                if not ready_connections:
                    break
                conn, *_ = ready_connections
                data = conn.recv()
                for conn_forward in connections:
                    if conn is not conn_forward:
                        conn_forward.send(data)
                return data
            except EOFError:
                del process._connections[conn]
                connections = list(MessageBusProcess.get_connections())


class SharedStore(dict):
    """
    A multi-process key-value store.

    Internally, the store uses ``MessageBusProcess`` for broadcasting updates
    by pipes. Generally speaking, the order of operations on the store is not
    preserved.

    Example:

        >>> def target(b1, b2, store):
        ...     b1.wait()
        ...     assert store['x'] == 1
        ...     del store['x']
        ...     b2.set()
        >>> store = SharedStore()
        >>> b1, b2 = multiprocessing.Event(), multiprocessing.Event()
        >>> child = MessageBusProcess(target=target, args=(b1, b2, store))
        >>> child.start()
        >>> store['x'] = 1
        >>> b1.set()
        >>> b2.wait()
        True
        >>> 'x' in store
        False
    """
    class UpdateType(enum.Enum):
        SET = enum.auto()
        DELETE = enum.auto()

    def update(self):
        while True:
            update = MessageBusProcess.consume(0)
            if not update:
                break
            update_type, key, *data = update
            if update_type is SharedStore.UpdateType.SET:
                super().__setitem__(key, data[0])
            elif update_type is SharedStore.UpdateType.DELETE:
                super().__delitem__(key)
            else:
                cls_name = self.__class__.__name__
                raise ValueError(f'Unknown {cls_name} update type "{update_type.name}".')

    def __getitem__(self, key):
        self.update()
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        self.update()
        MessageBusProcess.broadcast((SharedStore.UpdateType.SET, key, value))
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        self.update()
        MessageBusProcess.broadcast((SharedStore.UpdateType.DELETE, key))
        return super().__delitem__(key)

    def __contains__(self, key):
        self.update()
        return super().__contains__(key)


def load_schema(filename):
    _, extension = os.path.splitext(filename)
    with open(filename) as schema_file:
        if extension in ('.yml', '.yaml'):
            schema = yaml.load(schema_file)
        elif extension == '.json':
            schema = json.load(schema_file)
        else:
            raise Exception('Unknown schema file format of "{schema_filename}".')
    return schema
