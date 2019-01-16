"""
Smart Sensor messaging and parsing.

This module implements the Hibike protocol at the byte-level.
"""

from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from cython.parallel import parallel
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.string cimport memcpy
from collections.abc import MutableSequence


cpdef enum MessageType:
    PING = 0x10
    SUBSCRIBE_REQUEST = 0x11
    SUBSCRIBE_RESPONSE = 0x12
    DEV_READ = 0x13
    DEV_WRITE = 0x14
    DEV_DATA = 0x15
    DISABLE = 0x16
    HEARTBEAT_REQUEST = 0x17
    HEARTBEAT_RESPONSE = 0x18
    ERROR = 0xFF


cdef class BinaryRingBuffer:
    """
    In memory, the ring buffer '[1, 2, 3, 4]' could look like this:

        +---+---+---+- ... -+---+---+---+
        | 3 | 4 | - |       | - | 1 | 2 |
        +---+---+---+- ... -+---+---+---+
              ^                   ^
       End ---+                   +--- Start
    """
    cdef size_t start, end, capacity
    cdef uint8_t *buf

    def __cinit__(self, size_t capacity = 16384):
        self.start = self.end = 0
        self.capacity = capacity
        self.buf = <uint8_t *> PyMem_Malloc(capacity * sizeof(uint8_t))
        if not self.buf:
            raise MemoryError()

    def __dealloc__(self):
        PyMem_Free(self.buf)

    def __len__(self):
        if self.start <= self.end:
            return self.end - self.start
        return self.start + (self.capacity - self.end)

    def __getitem__(self, Py_ssize_t index):
        if index < len(self):
            return self.buf[(self.start + index) % self.capacity]
        raise IndexError()

    cpdef void extend(self, uint8_t *data, size_t size):
        # Equality is forbidden, since that would indicate an empty buffer,
        # not a full buffer.
        if len(self) + size >= self.capacity:
            raise MemoryError()
        cdef size_t tail_size
        if self.end + size >= self.capacity:
            tail_size = self.capacity - self.end
            memcpy(self.buf + self.end, data, tail_size)
            self.end = 0
            data += tail_size
            size -= tail_size
        memcpy(self.buf + self.end, data, size)
        self.end += size


cpdef void decode(BinaryRingBuffer buf) nogil:
    pass


# cdef struct SmartSensorUID:
#     uint16_t type
#     uint8_t year
#     uint64_t id
#
#
# cdef struct SmartSensorMessageHeader:
#     uint8_t message_id
#     uint8_t payload_len
#
#
# cpdef void test():
#     with nogil, parallel():
#         return


# cdef void compute_checksum(SmartSensorMessage *msg) nogil:
#     msg.checksum = msg.message_id ^ msg.payload_len
#     cdef uint16_t i
#     for i in range(msg.payload_len):
#         msg.checksum ^= msg.payload[i]


# cdef inline void make_ping(SmartSensorMessage *msg) nogil:
#     msg.message_id = PING
#     msg.payload_len = 0
#     compute_checksum(msg)
#
#
# cdef inline void make_disable(SmartSensorMessage *msg) nogil:
#     msg.message_id = DISABLE
#     msg.payload_len = 0
#     compute_checksum(msg)





# cdef class SmartSensorParser:
#     cpdef int parse(self) except *:
#         return 1


# cdef uint8_t checksum()

# class RingBuffer()

# cdef void nogil:
