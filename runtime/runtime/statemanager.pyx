# distutils: language = c++

from runtime.messaging import SharedMemoryBuffer, SharedRingBuffer


class ReadDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot read parameter "{param_name}" of sensor "{sensor_name}".')


class WriteDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot write parameter "{param_name}" of sensor "{sensor_name}".')


cdef class DeviceManager:
    def __cinit__(self, dict schema):
        pass

    def __dealloc__(self):
        pass


# def encode_loop(device_manager, ):
