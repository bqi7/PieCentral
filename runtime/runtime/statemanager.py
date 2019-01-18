from collections import namedtuple
import ctypes

import multiprocessing
import time

from numbers import Real
from typing import Dict, Tuple


Parameter = namedtuple('Parameter',
                       ['name', 'type', 'lower', 'upper', 'read', 'write'],
                       defaults=[float('-inf'), float('inf'), True, False])


class DeviceStructure(ctypes.Structure):
    """
    A struct representing a device (for example, a Smart Sensor).

    Example:

        >>> motor_type = DeviceStructure.make_device_type('YogiBear', {
        ...     'duty_cycle': Parameter('duty_cycle', ctypes.c_float, -1, 1)
        ... })
        >>> motor = multiprocessing.Value(motor_type, lock=False)
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

    @staticmethod
    def make_device_type(dev_name: str, params: Dict[str, Parameter]) -> type:
        """ Produce a named struct type. """
        fields = {}
        for param_name, param in params.items():
            fields[param_name] = param.type
            timestamp_name = DeviceStructure._get_timestamp_name(param_name)
            fields[timestamp_name] = ctypes.c_double
        return type(dev_name, (DeviceStructure,), {
            '_fields_': list(fields.items()),
            '_params': params,
        })


class StateManager:
    """
    A nested key-value store
    """
    def __init__(self):
        self._struct_cache = {}

    def __getitem__(self, lookup):
        if not isintance(lookup, tuple):
            lookup = (lookup, )

    def register_struct(self, name: str, params: dict):
        if name in self._struct_cache:
            raise KeyError(f'Structure "{name}" already exists.')
        self._struct_cache[name] = type(name, (DeviceStructure,),
                                        dict(_fields_=list(params.items())))
        device = multiprocessing.Value(self._struct_cache[name], lock=False)
        print(device.switch0)
        print(device.last_modified('switch0'))
