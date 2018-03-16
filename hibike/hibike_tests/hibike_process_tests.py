"""
Unit tests for functions in hibike_process.
"""
import unittest
import asyncio
import aioprocessing
import time
import serial
from spawn_virtual_devices import spawn_device, get_virtual_ports
from hibike_process_async import hotplug_async
import hibike_message as hm

class BasicHotplugTests(unittest.TestCase):
    """
    Tests for `hotplug_async`.
    """
    VIRTUAL_DEVICE_TYPES = ["LimitSwitch", "YogiBear", "YogiBear",
                            "RFID", "BatteryBuzzer"]
    VIRTUAL_DEVICE_STARTUP_TIME = 2
    IDENTIFY_TIMEOUT = 5
    VIRTUAL_DEVICE_CONFIG_FILE_PATH = "virtual_devices.txt"

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(lambda loop, context: None)
        self.devices = {}
        self.error_queue = asyncio.Queue(loop=self.loop)
        self.state_queue = aioprocessing.AioQueue()

    def tearDown(self):
        self.loop.stop()

    def write_out_virtual_devices(self, device_ports):
        """
        Notify Hibike of virtual devices on `device_ports`.
        """
        with open(self.VIRTUAL_DEVICE_CONFIG_FILE_PATH, "w") as vdev_file:
            vdev_file.write(" ".join(device_ports))
            vdev_file.flush()

    def identify_devices(self):
        """
        Try to identify virtual devices.
        """
        stop_task = None
        async def stop_event_loop():
            await asyncio.sleep(self.IDENTIFY_TIMEOUT, loop=self.loop)

        hotplug = self.loop.create_task(hotplug_async(self.devices, {}, self.error_queue,
                                                      self.state_queue, self.loop))
        stop_task = self.loop.create_task(stop_event_loop())
        _, pending = self.loop.run_until_complete(asyncio.wait([hotplug, stop_task],
                                                               return_when=asyncio.FIRST_COMPLETED,
                                                               loop=self.loop))
        for task in asyncio.Task.all_tasks(self.loop):
            task.cancel()
        try:
            self.loop.run_until_complete(asyncio.gather(*pending, loop=self.loop,
                                                        return_exceptions=True))
        except asyncio.CancelledError:
            self.loop.stop()


    def assert_all_devices_identified(self, identified_devices, msg=None):
        """
        Assert that IDENTIFIED_DEVICES contains all devices in
        VIRTUAL_DEVICE_TYPES.
        """
        device_ids = map(hm.uid_to_device_id, identified_devices)
        found_types = map(lambda dev: hm.DEVICES[dev]["name"], device_ids)
        self.assertListEqual(sorted(self.VIRTUAL_DEVICE_TYPES), sorted(found_types), msg)

    def test_detect_devices(self):
        """ Test detection of valid devices. """
        device_ports = []
        for vdev_type in self.VIRTUAL_DEVICE_TYPES:
            device_ports.append(spawn_device(vdev_type))
        self.write_out_virtual_devices(device_ports)
        # Wait for virtual devices to spin up
        time.sleep(self.VIRTUAL_DEVICE_STARTUP_TIME)
        self.identify_devices()
        self.assert_all_devices_identified(self.devices, "did not identify all sensors")

    def test_detect_no_devices(self):
        """ Make sure that we don't detect empty serial ports as sensors. """
        ports = []
        for _ in range(5):
            ports.append(serial.Serial(get_virtual_ports()[1]))
        self.write_out_virtual_devices(list(map(lambda p: p.name, ports)))
        self.identify_devices()
        self.assertEqual(self.devices, {}, "found smart sensor where there was none")

    def test_detect_some_devices(self):
        """
        Try detecting some devices when there are also empty
        serial ports.
        """
        ports = []
        devices = []
        for _ in range(5):
            ports.append(serial.Serial(get_virtual_ports()[1]))
        for vdev_type in self.VIRTUAL_DEVICE_TYPES:
            devices.append(serial.Serial(spawn_device(vdev_type)))
        self.write_out_virtual_devices(list(map(lambda d: d.name, devices)))
        time.sleep(self.VIRTUAL_DEVICE_STARTUP_TIME)
        self.identify_devices()
        self.assert_all_devices_identified(self.devices,
                                           "identified devices differs from spawned devices")
