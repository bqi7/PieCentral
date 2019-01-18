from libc.stdint cimport uint8_t
from libcpp.string cimport string
from posix.stat cimport mode_t
from posix.types cimport off_t


cdef extern from "<sys/mman.h>":
    int shm_open(const char *, int, mode_t)
    int shm_unlink(const char *)
    void *mmap(void *, size_t, int, int, int, off_t)
    int munmap(void *, size_t)
    enum: PROT_READ
    enum: PROT_WRITE
    enum: MAP_SHARED


cdef extern from "ringbuffer.cpp":
    pass


cdef extern from "ringbuffer.cpp" namespace "ringbuffer":
    cdef cppclass RingBuffer:
        RingBuffer(uint8_t *, size_t) except +
        size_t size()
        uint8_t operator[](size_t) except +
        void extend(string)
        string read()
