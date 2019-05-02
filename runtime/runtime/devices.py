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
import threading

from serial.tools.list_ports import comports
import yaml

from runtime.buffer import SharedMemory, MAX_PARAMETERS, BinaryRingBuffer
import runtime.journal
from runtime.messaging import Circuitbreaker
from runtime.packet import encode_loop, decode_loop
from runtime.util import RuntimeBaseException, read_conf_file

LOGGER = runtime.journal.make_logger(__name__)

try:
    from pyudev import Context, Devices, Device, Monitor, MonitorObserver
    udev_enabled = True
except ImportError:
    LOGGER.warning('Unable to import `pyudev`, which is Linux-only.')
    udev_enabled = False


Parameter = collections.namedtuple(
    'Parameter',
    ['name', 'type', 'lower', 'upper', 'readable', 'writeable'],
    defaults=[float('-inf'), float('inf'), True, False],
)


class SensorService(collections.UserDict):
    def __init__(self, schema_filename, dependents: set = None):
        self.dependents = {Circuitbreaker(path=path) for path in (dependents or {})}
        self.access, self.sensor_types = asyncio.Lock(), {}
        schema = read_conf_file(schema_filename)
        for dev_name, read_type, write_type in self.parse_schema(schema):
            self.sensor_types[dev_name] = read_type, write_type
        super().__init__()

    @staticmethod
    def parse_schema(schema):
        for _, devices in schema.items():
            for dev_name, device in devices.items():
                params = []
                for descriptor in device.get('params', ()):
                    attrs = {
                        'name': descriptor['name'],
                        'type': getattr(ctypes, f'c_{descriptor["type"]}'),
                    }
                    for attr in Parameter._fields[2:]:
                        if attr in descriptor:
                            attrs[attr] = descriptor[attr]
                    params.append(Parameter(**attrs))

                yield (
                    dev_name,
                    SensorReadStructure.make_type(dev_name, device['id'], params),
                    SensorWriteStructure.make_type(dev_name, device['id'], params),
                )

    async def register(self, uid: str):
        async with self.access:
            LOGGER.debug('Registered device.', uid=uid)
            for dependent in self.dependents:
                await dependent.register_device(uid)

    async def unregister(self, uid: str):
        async with self.access:
            LOGGER.debug('Unregistered device.', uid=uid)
            for dependent in self.dependents:
                await dependent.unregister_device(uid)

    async def write(self, uid: str, params):
        """ Issues a write command. """

    async def read(self, uid: str, params):
        """ Issues a read command. """

    async def collect(self, uid: str):
        pass

    def get_sensor_read_type(self, sensor_name):
        read_type, _ = self.sensor_types[sensor_name]
        return read_type

    def get_sensor_write_type(self, sensor_name):
        _, write_type = self.sensor_types[sensor_name]
        return write_type


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

    Attributes:
        read_buf (BinaryRingBuffer): Holds COBS-encoded packets just read.
        write_buf (BinaryRingBuffer): Holds COBS-encoded packets ready to be written.
    """
    def __init__(self, sensor_service):
        self.sensor_service = sensor_service
        # self.read_shm, self.write_shm =
        self.read_buf, self.write_buf = BinaryRingBuffer(), BinaryRingBuffer()
        self.encoder = threading.Thread(
            target=encode_loop,
            args=(),
        )
        self.decoder = threading.Thread(target=decode_loop)
        self.ready = asyncio.Event()

    def connection_made(self, transport):
        self.transport = transport
        transport.serial.rts = False
        LOGGER.debug('Connection made to serial.', com_port=transport.serial.port)
        self.handshake()
        self.ready.set()

    def handshake(self):
        pass

    def connection_lost(self, exc):
        LOGGER.debug('Connection to serial lost.', com_port=self.transport.serial.port)
        self.ready.clear()
        self.read_buf.clear()
        self.write_buf.clear()

    def data_received(self, data: bytes):
        self.read_buf.extend(data)

    async def send_messages(self):
        while self.ready.is_set() and not self.transport.is_closing():
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
    register_type = ctypes.c_uint64

    @staticmethod
    def _get_timestamp_name(param_name: str) -> str:
        return param_name + '_ts'

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
        super().__setattr__(param_name, value)

    def __getitem__(self, param_id):
        return self.__class__._params_by_id[param_id]

    @classmethod
    def make_type(cls, dev_name: str, dev_id: int, params: List[Parameter], *extra_fields) -> type:
        if len(params) > MAX_PARAMETERS:
            LOGGER.warning(
                'Device has too many parameters.',
                max_params=MAX_PARAMETERS,
                device=dev_name,
            )

        fields = list(extra_fields) or []
        for param in params:
            fields.extend([
                (param.name, param.type),
                (cls._get_timestamp_name(param.name), ctypes.c_double),
            ])

        return type(dev_name, (cls,), {
            '_dev_id': dev_id,
            '_fields_': fields,
            '_params': {param.name: param for param in params},
            '_params_by_id': params,
        })


class SensorReadStructure(SensorStructure):
    base_year = 2016  # Spring

    @property
    def uid(self):
        return self.dev_type << 72 | self.year_offset << 64 | self.id

    @property
    def year(self):
        return self.base_year + self.year_offset

    @staticmethod
    def make_type(dev_name: str, dev_id: int, params: List[Parameter]) -> type:
        return SensorStructure.make_type(
            dev_name.capitalize() + 'ReadStructure',
            dev_id,
            [param for param in params if param.readable],
            ('dev_type', ctypes.c_uint16),
            ('year_offset', ctypes.c_uint8),
            ('id', ctypes.c_uint64),
            ('delay', self.register_type),
            ('sub_params', self.register_type),
            ('heartbeat_id', ctypes.c_uint8),
            ('error_code', ctypes.c_uint8),
            ('sub_res_present', ctypes.c_bool),
            ('heartbeat_res_present', ctypes.c_bool),
            ('error_present', ctypes.c_bool),
        )


class SensorWriteStructure(SensorStructure):
    @staticmethod
    def make_type(dev_name: str, dev_id: int, params: List[Parameter]) -> type:
        return SensorStructure.make_type(
            dev_name.capitalize() + 'WriteStructure',
            dev_id,
            [param for param in params if param.writeable],
            ('write_flags', self.register_type),
            ('read_flags', self.register_type),
        )


def initialize_hotplugging(service, options):
    if options['poll'] or not udev_enabled:
        raise NotImplementedError('Polling-based hotplugging has not yet been implemented.')
    else:
        observer = SensorObserver(service, options['baud_rate'])
        observer.start()
        observer.load_initial_sensors()


async def log_statistics(period):
    while True:
        LOGGER.debug('Device statistics.')
        await asyncio.sleep(period)


async def start(options):
    service = SensorService(options['dev_schema'], {options['exec_srv'], options['net_srv']})
    initialize_hotplugging(service, options)
    client = Circuitbreaker(host=options['host'], port=options['tcp'])
    try:
        await log_statistics(options['stat_period'])
    except asyncio.CancelledError:
        observer.stop()
