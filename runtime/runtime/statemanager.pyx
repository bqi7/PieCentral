# distutils: language = c++

from libc.string cimport strcpy
from libc.stdint cimport uint8_t, uint64_t
from posix.fcntl cimport O_CREAT, O_RDWR
from posix.stat cimport mode_t, S_IRUSR, S_IWUSR
from posix.unistd cimport ftruncate
from posix.types cimport off_t
from cpython.mem cimport PyMem_Malloc, PyMem_Free
# from runtime.packet cimport ParameterType, parameter, size_of_type


cdef extern from "<sys/mman.h>":
    int shm_open(const char *, int, mode_t)
    int shm_unlink(const char *)
    void *mmap(void *, size_t, int, int, int, off_t)
    int munmap(void *, size_t)
    enum: PROT_READ
    enum: PROT_WRITE
    enum: MAP_SHARED


class ReadDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot read parameter "{param_name}" of sensor "{sensor_name}".')


class WriteDisabledError(Exception):
    def __init__(self, sensor_name, param_name):
        super().__init__(f'Cannot write parameter "{param_name}" of sensor "{sensor_name}".')


cdef class SharedMemoryBuffer:
    _SHM_NAME_BASE = 'runtime-shm-buf'
    cdef Py_ssize_t size
    cdef char *name
    cdef int fd
    cdef uint8_t *mem_buf

    def __cinit__(self, str name, Py_ssize_t size):
        self.size = size

        full_name = self._SHM_NAME_BASE + '-' + name
        self.name = <char *> PyMem_Malloc(self.size * (len(full_name) + 1))
        if not self.name:
            raise MemoryError('Failed to allocate memory for shared memory object name.')
        strcpy(self.name, full_name.encode('utf-8'))

        self.fd = shm_open(self.name, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        if self.fd == -1:
            raise OSError('Failed to open shared memory object.')
        ftruncate(self.fd, size)

        self.mem_buf = <uint8_t *> mmap(NULL, size, PROT_READ | PROT_WRITE,
                                        MAP_SHARED, self.fd, 0)

    def __dealloc__(self):
        err = None
        if munmap(self.mem_buf, self.size):
            err = 'Failed to munmap buffer in memory.'
        if shm_unlink(self.name):
            err = 'Failed to unlink shared memory object.'
        PyMem_Free(self.name)
        if err:
            raise OSError(err)

    @property
    def fileno(self):
        return self.fd

    def _check_bounds(self, index):
        if not 0 <= index < self.size:
            raise IndexError()

    def __getitem__(self, Py_ssize_t index):
        self._check_bounds(index)
        return self.mem_buf[index]

    def __setitem__(self, Py_ssize_t index, uint8_t byte):
        self._check_bounds(index)
        self.mem_buf[index] = byte


# cdef class DeviceManager:
#     _SHM_NAME_BASE = 'rtd-statemanager'
#     cdef:
#         int shm_fd
#         size_t num_params
#
#     cdef write(self):
#         # cdef
#         # struct.pack()
#         pass



# cdef class SensorManager:
#     _SHM_NAME_BASE = 'rtd-statemanager'
#     cdef:
#         int shm_fd
#         size_t num_params
#         ParameterType *param_types
#
#     def __cinit__(self, sensor_uid uid, list param_types):
#         self.num_params = len(param_types)
#         self.param_types = (<ParameterType *>
#             PyMem_Malloc(sizeof(ParameterType) * self.num_params))
#         for param_type in param_types:
#             self.param_types[i] = param_types[i]
#
#     def __dealloc__(self):
#         PyMem_Free(self.param_types)


# cdef struct sensor_descriptor:
#     bint valid
#     sensor_uid uid
#
#
# cdef class DeviceManager:
#     _SHM_NAME_BASE = 'rtd-statemanager'
#     cdef:
#         int shm_fd
#         char *shm_name
#         size_t max_sensors
#         sensor_descriptor *sensors
#         size_t num_params
#         ParameterType *param_types
#
#     cdef _init_sensor_descriptors(self, size_t max_sensors):
#         self.max_sensors = max_sensors
#         self.sensors = (<sensor_descriptor *>
#             PyMem_Malloc(sizeof(sensor_descriptor) * self.max_sensors))
#         for i in range(max_sensors):
#             self.sensors[i].valid = False
#
#     cdef _init_param_types(self, list param_types):
#         self.num_params = len(param_types)
#         self.param_types = (<ParameterType *>
#             PyMem_Malloc(sizeof(ParameterType) * self.num_params))
#         for i in range(self.num_params):
#             self.param_types[i] = param_types[i]
#
#     def __cinit__(self, str device_name, size_t max_sensors, list param_types):
#         shm_name = self._SHM_NAME_BASE + '-' + device_name
#         self.shm_name = <char *> PyMem_Malloc(sizeof(char) * (len(shm_name) + 1))
#         if not self.shm_name:
#             raise MemoryError()
#         strcpy(self.shm_name, shm_name.encode('utf-8'))
#
#         self._init_sensor_descriptors(max_sensors)
#         self._init_param_types(param_types)
#
#         self.shm_fd = shm_open(self.shm_name, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
#         if self.shm_fd == -1:
#             raise OSError('Failed to open shared memory object.')
#         # ftruncate(self.shm_fd, )
#
#     def __dealloc__(self):
#         if shm_unlink(self.shm_name) != 0:
#             raise OSError('Failed to unlink shared memory object.')
#         PyMem_Free(self.shm_name)
#         PyMem_Free(self.param_types)
#         PyMem_Free(self.sensors)
#
#
# class StateManager:
#     def __init__(self, schema):
#         self.dev_managers = {sensor: DeviceManager(sensor) for sensor in schema}
