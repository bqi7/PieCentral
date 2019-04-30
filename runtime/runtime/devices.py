"""
This module manages Smart Sensor communication.
"""


__all__ = ['SmartSensorObserver']

import asyncio
import collections
import functools
from numbers import Real
from typing import List, Callable, Generator, Sequence
import ctypes
import os
import socket
import serial
import serial_asyncio
import time

from serial.tools.list_ports import comports
import yaml

from runtime.buffer import SharedMemory, MAX_PARAMETERS, ParameterStatus, BinaryRingBuffer
import runtime.journal
from runtime.messaging import Circuitbreaker
from runtime.packet import write_loop, decode_loop
from runtime.util import RuntimeBaseException

LOGGER = runtime.journal.make_logger(__name__)

try:
    from pyudev import Context, Devices, Device, Monitor, MonitorObserver
    udev_enabled = True
except ImportError:
    LOGGER.warning('Unable to import `pyudev`, which is Linux-only.')
    udev_enabled = False


Parameter = collections.namedtuple(
    'Parameter',
    ['name', 'type', 'lower', 'upper', 'readable', 'writeable', 'choices', 'default'],
    defaults=[float('-inf'), float('inf'), True, False, [], None],
)

CTYPES_SIGNED_INT = {ctypes.c_byte, ctypes.c_short, ctypes.c_int, ctypes.c_long,
                     ctypes.c_longlong, ctypes.c_ssize_t}
CTYPES_UNSIGNED_INT = {ctypes.c_ubyte, ctypes.c_ushort, ctypes.c_uint,
                       ctypes.c_ulong, ctypes.c_ulonglong, ctypes.c_size_t}
CTYPES_REAL = {ctypes.c_float, ctypes.c_double, ctypes.c_longdouble}
CTYPES_NUMERIC = CTYPES_SIGNED_INT | CTYPES_UNSIGNED_INT | CTYPES_REAL


class SensorService(collections.UserDict):
    def __init__(self, dependents: set = None):
        dependents  = dependents or {}
        self.dependents = {Circuitbreaker(path=path) for path in dependents}
        self.access = asyncio.Lock()
        super().__init__()

    async def register_device(self, uid: str):
        async with self.access:
            LOGGER.debug('Registered device.')
            for dependent in self.dependents:
                await dependent.register_device(uid)

    async def unregister_device(self, uid: str):
        async with self.access:
            LOGGER.debug('Unregistered device.')
            for dependent in self.dependents:
                await dependent.unregister_device(uid)

    async def write(self, uid: str, params):
        pass

    async def read(self, uid: str):
        pass


class SensorObserver(MonitorObserver):
    subsystem, device_type = 'usb', 'usb_interface'

    def __init__(self, sensor_service: SensorService, baud_rate: int, thread_name: str = 'device-observer'):
        self.loop = asyncio.get_event_loop()
        self.sensor_service, self.baud_rate = sensor_service, baud_rate
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
        make_protocol = lambda: SensorProtocol(self.sensor_service)
        conn = serial_asyncio.create_serial_connection(self.loop, make_protocol,
                                                       com_port, baudrate=self.baud_rate)
        asyncio.ensure_future(conn, loop=self.loop)

    def handle_hotplug_event(self, action, device):
        path, product = device.sys_path, device.properties.get('PRODUCT')
        if self.is_sensor(device):
            if action.lower() == 'add':
                for com_port in self.get_com_ports({device}):
                    self.open_serial_conn(com_port)
                return
            elif action.lower() == 'remove':
                return
        LOGGER.debug('Ignoring irrelevant hotplug event.',
                     action=action, path=path, product=product)

    def load_initial_sensors(self):
        for com_port in self.get_com_ports(self.list_devices()):
            self.open_serial_conn(com_port)


class SensorProtocol(asyncio.Protocol):
    """
    An implementation of the Smart Sensor protocol.
    """
    def __init__(self, service):
        self.service = service
        self.buffer = BinaryRingBuffer()
        self.ready = asyncio.Event()

    def connection_made(self, transport):
        self.transport = transport
        transport.serial.rts = False
        LOGGER.debug('Connection made to serial transport.', com_port=transport.serial.port)
        self.write_queue = BinaryRingBuffer()
        LOGGER.debug('Initialized read and write queues.', com_port=transport.serial.port)
        self.handshake()

    def handshake(self):
        self.ready.set()

    def connection_lost(self, exc):
        LOGGER.debug('Connection to serial transport lost.')
        self.ready.clear()

    def data_received(self, data: bytes):
        pass

    def eof_received(self):
        pass

    async def send_messages(self):
        while True:
            packet = self.write_queue.read()
            self.transport.write(packet)


class SensorStructure(ctypes.LittleEndianStructure):
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
    @staticmethod
    def _get_timestamp_name(param_name: str) -> str:
        return param_name + '_ts'

    @staticmethod
    def _get_status_name(param_name: str) -> str:
        return param_name + '_status'

    def last_modified(self, param_name: str) -> float:
        return getattr(self, self._get_timestamp_name(param_name))

    def __setattr__(self, param_name: str, value):
        """ Validate and assign the parameter's value, and update its timestamp. """
        if isinstance(value, Real):
            param = self._params[param_name]
            if not param.lower <= value <= param.upper:
                cls_name = self.__class__.__name__
                raise ValueError(f'Assigned invalid value {value} to '
                                 f'"{cls_name}.{param_name}" (not in bounds).')
        super().__setattr__(self._get_timestamp_name(param_name), time.time())
        status_name = self._get_status_name(param_name)
        super().__setattr__(status_name, getattr(self, status_name) | ParameterStatus.DIRTY)
        super().__setattr__(param_name, value)

    def __getitem__(self, param_id):
        return self.__class__._params_by_id[param_id]

    @classmethod
    def make_sensor_type(cls, dev_name: str, params: List[Parameter]) -> type:
        if len(params) > MAX_PARAMETERS:
            raise RuntimeBaseException('Device has too many parameters.',
                                       max_params=MAX_PARAMETERS)
        fields = []
        for param in params:
            fields.extend([
                (param.name, param.type),
                (cls._get_timestamp_name(param.name), ctypes.c_double),
                (cls._get_status_name(param.name), ctypes.c_uint8),
            ])
        return type(dev_name, (SensorStructure,), {
            '_fields_': fields,
            '_params': {param.name: param for param in params},
            '_params_by_id': params
        })

    def __getstate__(self):
        device_type = type(self)
        return device_type.__name__, device_type._params_by_id, self._buf

    def __setstate__(self, state):
        pass


def initialize_hotplugging(service, options):
    if options['poll'] or not udev_enabled:
        pass
    else:
        observer = SensorObserver(service, options['baud_rate'])
        observer.start()
        observer.load_initial_sensors()


async def log_statistics(period):
    while True:
        LOGGER.debug('Device statistics.')
        await asyncio.sleep(period)


async def start(options):
    service = SensorService({options['exec_srv'], options['net_srv']})
    initialize_hotplugging(service, options)
    client = Circuitbreaker(host=options['host'], port=options['tcp'])
    try:
        await log_statistics(options['stat_period'])
    except asyncio.CancelledError:
        observer.stop()
