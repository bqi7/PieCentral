# distutils: language = c++

"""
Runtime buffer module.
"""

from libc.errno cimport errno, ENOENT
from libc.string cimport strcpy
from libc.stdint cimport uint8_t
from libcpp.string cimport string
from posix.unistd cimport ftruncate

cimport cython
from cython.operator cimport dereference as deref
from cpython cimport Py_buffer
from cpython.buffer cimport PyBUF_ND
from cpython.mem cimport PyMem_Malloc, PyMem_Free


cdef class SharedMemoryBuffer:
    """
    A fixed-length binary buffer.

    This object supports the pickling and writeable buffer protocols.
    """
    _SHM_NAME_BASE = 'runtime-shm-buf'
    cdef Py_ssize_t size
    cdef char *name
    cdef int fd
    cdef uint8_t *buf
    cdef Py_ssize_t shape[1]
    cdef Py_ssize_t ref_count

    def __cinit__(self, str name, Py_ssize_t size):
        self.size = size
        self.shape[0] = size
        self.ref_count = 0

        full_name = self._SHM_NAME_BASE + '-' + name
        self.name = <char *> PyMem_Malloc(len(full_name) + 1)
        if not self.name:
            raise MemoryError('Failed to allocate memory for shared memory object name.')
        strcpy(self.name, full_name.encode('utf-8'))

        self.fd = shm_open(self.name, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
        if self.fd == -1:
            raise OSError('Failed to open shared memory object.')
        ftruncate(self.fd, size)

        self.buf = <uint8_t *> mmap(NULL, size, PROT_READ | PROT_WRITE,
                                    MAP_SHARED, self.fd, 0)

    def __dealloc__(self):
        message = None
        if munmap(self.buf, self.size):
            message = 'Failed to munmap buffer in memory.'
        # Ignore error if another buffer pointing at the same shared memory
        # has already unlinked it. It is fine to open and unlink the same
        # shared memory object multiple times.
        if shm_unlink(self.name) and errno != ENOENT:
            message = 'Failed to unlink shared memory object.'
        # Violating this condition means there are serious memory issues.
        if self.ref_count > 0:
            message = 'One or more memory views are still in use.'

        PyMem_Free(self.name)
        if message:
            raise OSError(message)

    @property
    def fileno(self):
        return self.fd

    cdef _check_bounds(self, index):
        if not 0 <= index < self.size:
            raise IndexError()

    def __getitem__(self, Py_ssize_t index):
        self._check_bounds(index)
        return self.buf[index]

    def __setitem__(self, Py_ssize_t index, uint8_t byte):
        self._check_bounds(index)
        self.buf[index] = byte

    def __reduce__(self):
        suffix = self.name.decode('utf-8')[len(self._SHM_NAME_BASE)+1 :]
        return SharedMemoryBuffer, (suffix, self.size)

    def __getbuffer__(self, Py_buffer *buffer, int flags):
        if not (flags & PyBUF_ND):
            raise BufferError()
        buffer.buf = <char *> self.buf
        buffer.format = 'c'
        buffer.internal = NULL
        buffer.itemsize = sizeof(uint8_t)
        buffer.len = buffer.itemsize * self.size
        buffer.ndim = 1
        buffer.obj = self
        buffer.readonly = 0
        buffer.shape = self.shape
        buffer.strides = NULL
        buffer.suboffsets = NULL
        self.ref_count += 1

    def __releasebuffer__(self, Py_buffer *buffer):
        self.ref_count -= 1


@cython.final
cdef class BinaryRingBuffer:
    DEFAULT_CAPACITY = 16 * 1024
    cdef RingBuffer *buf

    def __cinit__(self, size_t capacity = DEFAULT_CAPACITY):
        self.buf = new RingBuffer(capacity)

    def __dealloc__(self):
        del self.buf

    def __len__(self):
        return self.buf.size()

    def __getitem__(self, index):
        return deref(self.buf)[index]

    cpdef void extend(self, string buf) nogil:
        self.buf.extend(buf)

    cpdef string read(self) nogil:
        """ Reads the next zero-delimited sequence, blocking if necessary. """
        return self.buf.read()
