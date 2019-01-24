from collections import namedtuple, UserDict
import ctypes
from functools import lru_cache, partial
import enum

import os
import json
import multiprocessing
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
        >>> list(MessageBusProcess.consume())
        ['OK!']
        >>> child.join()
        >>> child.close()
    """
    def __init__(self, *args, **kwargs):
        conn_to_parent, conn_to_child = multiprocessing.Pipe()
        parent = multiprocessing.current_process()
        if not hasattr(parent, '_connections'):
            parent._connections = []
        terminated = multiprocessing.Event()
        parent._connections.append((conn_to_child, terminated))
        self._connections = [(conn_to_parent, terminated)]
        super().__init__(*args, **kwargs)

    def close(self):
        for _, terminated in getattr(self, '_connections', []):
            terminated.set()
        super().close()

    @staticmethod
    def get_connections():
        process = multiprocessing.current_process()
        connections = getattr(process, '_connections', [])
        valid_conn = lambda conn: not conn[1].is_set()
        process._connections = list(filter(valid_conn, connections))
        for conn, _ in process._connections:
            yield conn

    @staticmethod
    def broadcast(data):
        for conn in MessageBusProcess.get_connections():
            conn.send(data)

    @staticmethod
    def consume():
        for conn in MessageBusProcess.get_connections():
            while conn.poll():
                yield conn.recv()


"""
class MessageBus(BaseQueue):
    def __init__(self, *args, **kwargs):
        self.primary_pid = os.getpid()
        super().__init__(*args, **kwargs)

    @property
    def primary(self):
        return self.primary_pid == os.getpid()

    def make_replica_process(self, target: Callable[[MessageBus, ...], ...],
                             args=None, kwargs=None, name=None, daemon=None):
        if not self.primary:
            raise RuntimeError('Only primary process may create replicas.')
        args, kwargs = (self,) + (args or ()), kwargs or {}
        recv_conn, send_conn =
        return multiprocessing.Process(target=target, args=args, kwargs=kwargs,
                                       name=name, daemon=daemon)


class SharedStore(UserDict, BaseQueue):
    class UpdateType(enum.Enum):
        SET = enum.auto()
        UPDATE = enum.auto()
        SUBSCRIBE = enum.auto()
        UNSUBSCRIBE = enum.auto()

    def update(self):
        pass

    def __init__(self):
        pass

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
"""


# import time
# store = SharedStore()
# def target(store):
#     time.sleep(3)
# child1 = multiprocessing.Process(target=target, args=(store,))
# child1.start()
# child2 = multiprocessing.Process(target=target, args=(store,))
# child2.start()
# child1.join()
# child2.join()


# class SharedStore(UserDict):
#     """
#     A multi-process key-value store.
#
#     The internal architecture follows the primary/replica model, where one
#     process is designated to have an authoritative copy of the store. The
#     replicas subscribe and publish changes to the primary. Changes made by one
#     replica are broadcast to the other replicas. All communication is done over
#     duplex pipes::
#
#                      +---------+
#               +----->| Primary |<-----+
#               |      +---------+      |
#               V                       V
#         +-----------+           +-----------+
#         | Replica 1 |    ...    | Replica N |
#         +-----------+           +-----------+
#
#     Example:
#
#         >>> store = SharedStore()
#         >>> store['a', 'b', 0x100] = 1
#         >>> def target(store):
#         ...     assert not store.is_primary
#         ...     assert store['a', 'b', 0x100] == 1
#         ...     store['a', 'b', 0x101] = 2
#         >>> child = multiprocessing.Process(target=target, args=(store,))
#         >>> child.start()
#         >>> child.join()
#         >>> store['a', 'b', 0x101]
#         2
#     """
#     class UpdateType(enum.Enum):
#         SET = enum.auto()
#         DELETE = enum.auto()
#         SUBSCRIBE = enum.auto()
#         UNSUBSCRIBE = enum.auto()
#
#     Update = namedtuple('Update', ['type', 'pid', 'data'])
#
#     def __init__(self):
#         self.primary_pid = os.getpid()
#         self.ready = multiprocessing.Event()
#         self.update_queue = multiprocessing.Queue()
#         self.update_thread = threading.Thread(target=self.update)
#         self.update_thread.daemon = True
#         self.update_thread.start()
#         self.update_thread.join()
#
#     @property
#     def primary(self):
#         return os.getpid() == self.primary_pid
#
#     def _send_update(self, update_type, *data):
#         if not self.primary:
#             update = Update(update_type, os.getpid(), data)
#             self.update_queue.put(update, block=False)
#             self.ready.clear()
#
#     def update(self):
#         if self.primary:
#             while True:
#                 update = self.update_queue.get()
#         else:
#             pass
#
#     """
#     def __init__(self):
#         self.primary_pid = os.getpid()
#         self.ready = multiprocessing.Event()
#         self.ready.set()
#         self.update_queue = multiprocessing.Queue()
#         self.connections = {}
#         super().__init__()
#
#     @property
#     def primary(self):
#         return os.getpid() == self.primary_pid
#
#     def _send_update(self, update_type, *data):
#         if not self.primary:
#             update = Update(update_type, os.getpid(), data)
#             self.update_queue.put(update)
#             self.ready.clear()
#
#     def _apply_update(self, update):
#         if update.type is UpdateType.SET:
#             key, value = update.data
#             self.data[key] = value
#         elif update.type is Update.DELETE:
#             key, *_ = update.data
#             del self.data[key]
#         else:
#             raise ValueError(f'Cannot apply update with type "{update.type}".')
#
#     def _replica_update(self):
#         if not hasattr(self, 'recv_conn'):
#             self.recv_conn, send_conn = multiprocessing.Pipe(duplex=False)
#             self._send_update(UpdateType.SUBSCRIBE, send_conn)
#         self.ready.wait()
#
#     def _primary_update(self):
#         while not self.update_queue.empty():
#             try:
#                 update = self.update.get(block=False)
#             except queue.Empty:
#                 break
#             if update.type is UpdateType.SUBSCRIBE:
#                 conn, *_ = update.data
#                 self.connections[update.pid] = conn
#             elif update.type is UpdateType.UNSUBSCRIBE:
#                 del self.connections[update.pid]
#             else:
#                 self._apply_update(update)
#
#     def _broadcast(self, update):
#         for pid, conn in self.connections.items():
#             conn
#
#     def _update(self):
#         if self.primary:
#             self._primary_update()
#         else:
#             self._replica_update()
#
#     def __setitem__(self, key, value):
#         self._update()
#         super().__setitem__(key, value)
#         self._send_update(UpdateType.SET, key, value)
#
#     def __getitem__(self, key):
#         self._update()
#         return super().__getitem__(key)
#
#     def __delitem__(self, key):
#         self._update()
#         super().__delitem__(key)
#         self._send_update(UpdateType.DELETE, key)
#
#     def __del__(self):
#         self._send_update(UpdateType.UNSUBSCRIBE)
#     """


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
