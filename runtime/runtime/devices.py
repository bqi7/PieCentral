"""
This module manages Smart Sensor communication.
"""


__all__ = ['SmartSensorObserver']


import asyncio
from collections import namedtuple
import ctypes
from typing import List
import os
import serial
# from serial.aio import create_serial_connection
# from serial.tools.list_ports import comports
from typing import Callable, Generator
from runtime.logging import make_logger
import yaml
import time

LOGGER = make_logger(__name__)

try:
    from pyudev import Context, Devices, Device, Monitor, MonitorObserver
except ImportError:
    LOGGER.warning('Unable to import `pyudev`, which is Linux-only.')


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


def is_sensor_device(vendor_id: int, product_id: int) -> bool:
    """
    Determine whether the USB descriptor belongs to an Arduino Micro (CDC ACM).

    .. _Linux USB Project ID List
        http://www.linux-usb.org/usb.ids
    """
    return vendor_id == 0x2341 and product_id == 0x8037


def load_schema(schema_path):
    with open(schema_path, 'r') as schema_file:
        schema = yaml.load(schema_file)
    for device in schema.values():
        for param in device['params']:
            if 'read' not in param:
                param['read'] = True
            if 'write' not in param:
                param['write'] = False
            # TODO: add default lower and upper bounds
    print(base_schema)


def start(poll, poll_period, encoders, decoders):
    while True:
        pass


def bootstrap(options):
    # event_loop = asyncio.get_event_loop()
    # event_loop.run_forever()
    default_schema_path = os.path.join(os.path.dirname(__file__), 'devices.yaml')
    schema = load_schema(default_schema_path)


if __name__ == '__main__':
    # cli()
    bootstrap({})
