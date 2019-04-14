"""
This module manages Smart Sensor communication.
"""


__all__ = ['SmartSensorObserver']

import asyncio
import collections
from typing import List, Callable, Generator, Sequence
import ctypes
import os
import socket
import serial
import serial_asyncio
import time

import yaml
from runtime.buffer import SharedMemoryBuffer
import runtime.journal
from runtime.networking import ClientCircuitbreaker
from runtime.store import Parameter

# from serial.aio import create_serial_connection
from serial.tools.list_ports import comports

LOGGER = runtime.journal.make_logger(__name__)

try:
    from pyudev import Context, Devices, Device, Monitor, MonitorObserver
except ImportError:
    LOGGER.warning('Unable to import `pyudev`, which is Linux-only.')


class SensorService:
    def __init__(self):
        self.access = asyncio.Lock()
        self.read_buffers, self.write_buffers, self.locks = {}, {}, {}
        super().__init__()

    async def register_device(self, uid: str):
        async with self.access:
            self.read_buffers[uid] = None
            self.write_buffers[uid] = None

    async def unregister_device(self):
        async with self.access:
            del self.read_buffers[uid]
            del self.write_buffers[uid]

    async def write(self, uid: str, params):
        pass

    async def read(self, uid: str):
        pass


class SensorObserver(MonitorObserver):
    subsystem, device_type = 'usb', 'usb_interface'

    def __init__(self, service: SensorService, baud_rate: int, thread_name: str = 'device-observer'):
        self.loop = asyncio.get_event_loop()
        self.service, self.baud_rate = service, baud_rate
        self.thread_name, self.context = thread_name, Context()
        self.monitor = Monitor.from_netlink(self.context)
        self.monitor.filter_by(self.subsystem, self.device_type)
        super().__init__(self.monitor, self.handle_hotplug_event, name=self.thread_name)

    def list_devices(self) -> Generator[Device, None, None]:
        for device in self.context.list_devices(subsystem=self.subsystem):
            if self.is_sensor(device):
                yield device

    @staticmethod
    def is_sensor(device: Device) -> bool:
        """
        Determine whether the USB descriptor belongs to an Arduino Micro (CDC ACM).

        .. _Linux USB Project ID List
            http://www.linux-usb.org/usb.ids
        """
        try:
            vendor_id, product_id, _ = device.properties['PRODUCT'].split('/')
            return int(vendor_id, 16) == 0x2341 and int(product_id, 16) == 0x8037
        except (KeyError, ValueError):
            return False

    @staticmethod
    def get_com_ports(devices: Sequence[Device]):
        """ Translate a sequence of `pyudev` devices into usable COM ports. """
        ports = serial.tools.list_ports.comports(include_links=True)
        port_devices = {port.location: port.device for port in ports}
        for device in devices:
            for filename in os.listdir(device.sys_path):
                if filename.startswith('tty'):
                    for port in ports:
                        if port.location in device.sys_path:
                            yield port.device
                            break

    def open_serial_conn(self, com_port: str):
        """ Create a serial connection and add it to the running event loop. """
        LOGGER.debug('Creating serial connection.', com_port=com_port, baud_rate=self.baud_rate)
        conn = serial_asyncio.create_serial_connection(self.loop, SensorProtocol,
                                                       com_port, baudrate=self.baud_rate)
        asyncio.ensure_future(conn, loop=self.loop)

    def handle_hotplug_event(self, action, device):
        if self.is_sensor(device):
            if action == 'add':
                for com_port in self.get_com_ports({device}):
                    self.open_serial_conn(com_port)
            elif action == 'remove':
                pass
            else:
                LOGGER.debug('Ignoring irrelevant hotplug event.', action=action)
        else:
            # For debugging erroneously ignored sensors.
            LOGGER.debug('Ignoring non-sensor hotplug event.',
                         path=device.sys_path, product=device.properties.get('PRODUCT'))

    def load_initial_sensors(self):
        for com_port in self.get_com_ports(self.list_devices()):
            self.open_serial_conn(com_port)


class SensorProtocol(asyncio.Protocol):
    def __init__(self):
        pass

    def connection_made(self, transport):
        self.transport = transport
        LOGGER.debug('Connection made to sensor transport.')

    def connection_lost(self, exc):
        pass

    def data_received(self, data: bytes):
        pass

    def eof_received(self):
        pass


class SensorStructure(ctypes.Structure):
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
        """ Produce and defines a named struct type. """
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

    def __getstate__(self):
        device_type = type(self)
        return device_type.__name__, device_type._params_by_id, self._buf

    def __setstate__(self, state):
        pass


async def start(options):
    sensor_service = SensorService()
    observer = SensorObserver(sensor_service, options['baud_rate'])
    observer.start()
    observer.load_initial_sensors()
    client = ClientCircuitbreaker(host=options['host'], port=options['tcp'])
    try:
        while True:
            pass
    except asyncio.CancelledError:
        observer.stop()

    # LOGGER.debug(f'{list(get_com_ports(observer.list_sensors()))}')
    # observer.join()

    # await client.set_alliance('blue')
    # while True:
    #     await asyncio.sleep(1)
    #     LOGGER.info(str(await client.get_field_parameters()))


if __name__ == '__main__':
    def callback(device):
        print(device.device_path)
    observer = SmartSensorObserver(callback)
    observer.start()
    observer.join()
