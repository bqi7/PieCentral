# distutils: language = c++

"""
Runtime module for encoding and decoding Smart Sensor messages.
"""

from runtime.buffer cimport SharedMemoryBuffer, BinaryRingBuffer


cpdef enum PacketType:
    PING          = 0x10
    SUB_REQ       = 0x11
    SUB_RES       = 0x12
    DEV_READ      = 0x13
    DEV_WRITE     = 0x14
    DEV_DATA      = 0x15
    DEV_DISABLE   = 0x16
    HEARTBEAT_REQ = 0x17
    HEARTBEAT_RES = 0x18
    ERROR         = 0xFF


cdef class Parameter:
    pass


cpdef void encode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer write_queue) nogil:
    while True:
        pass


cpdef void decode_spin(SharedMemoryBuffer sm_buf, BinaryRingBuffer read_queue) nogil:
    while True:
        pass
