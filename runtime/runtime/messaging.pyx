# distutils: language = c++

"""
Runtime IPC module.
"""

from libc.string cimport strcpy
from libc.stdint cimport uint8_t, uint64_t
from posix.fcntl cimport O_CREAT, O_RDWR
from posix.stat cimport mode_t, S_IRUSR, S_IWUSR
from posix.unistd cimport ftruncate
from posix.types cimport off_t
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from cython.operator cimport dereference as deref
from libcpp.string cimport string
from runtime.messaging cimport RingBuffer


cdef class SharedRingBuffer:
    DEFAULT_CAPACITY = 16 * 1024
    cdef SharedMemoryBuffer shm
    cdef RingBuffer *buf

    def __cinit__(self, str name, size_t capacity = DEFAULT_CAPACITY):
        self.shm = SharedMemoryBuffer(name, capacity)
        self.buf = new RingBuffer(self.shm.mem_buf, capacity)

    def __dealloc__(self):
        del self.buf

    def __len__(self):
        return self.buf.size()

    def __getitem__(self, Py_ssize_t index):
        return deref(self.buf)[index]

    cpdef extend(self, string buf):
        self.buf.extend(buf)


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
