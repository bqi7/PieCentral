"""
This module manages Smart Sensor communication.
"""


__all__ = ['SmartSensorObserver']


import asyncio
import os
import serial
from serial.aio import create_serial_connection
from serial.tools.list_ports import comports
from typing import Callable, Generator
from runtime.logging import make_logger

LOGGER = make_logger(__name__)

try:
    from pyudev import Context, Devices, Device, Monitor, MonitorObserver
except ImportError:
    LOGGER.warning('Unable to import `pyudev`, which is Linux-only.')


def is_sensor_device(vendor_id: int, product_id: int) -> bool:
    """
    Determine whether the USB descriptor belongs to an Arduino Micro (CDC ACM).

    .. _Linux USB Project ID List
        http://www.linux-usb.org/usb.ids
    """
    return vendor_id == 0x2341 and product_id == 0x8037


def bootstrap(options):
    event_loop = asyncio.get_event_loop()
    event_loop.run_forever()


if __name__ == '__main__':
    # cli()
    bootstrap({})
