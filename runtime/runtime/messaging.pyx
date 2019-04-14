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


def map_parameters():
    pass


cdef void _encode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer write_queue) nogil:
    while True:
        pass


from libc.stdio cimport printf
from posix.unistd cimport usleep
cdef void _decode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer read_queue) nogil:
    while True:
        # packet = read_queue.read()
        printf("OK!\n")
        usleep(100000)


def encode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer write_queue):
    with nogil:
        _encode_loop(sm_buf, write_queue)


def decode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer read_queue):
    with nogil:
        _decode_loop(sm_buf, read_queue)
