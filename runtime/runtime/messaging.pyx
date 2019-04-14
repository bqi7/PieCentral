# distutils: language = c++

"""
Runtime module for encoding and decoding Smart Sensor messages.
"""

from libc.stdint cimport uint8_t, uint16_t, uint64_t
from libcpp.string cimport string
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


cpdef uint8_t compute_checksum(string message) nogil:
    cdef uint8_t checksum = 0
    for i in range(message.size()):
        checksum ^= message[i]
    return checksum


cdef void _encode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer write_queue) nogil:
    while True:
        pass


cdef void _decode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer read_queue) nogil:
    while True:
        packet = read_queue.read()
        packet = cobs_decode(packet)
        if packet.size() < 3:
            continue
        checksum = compute_checksum(packet.substr(0, packet.size() - 1))


def encode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer write_queue):
    with nogil:
        _encode_loop(sm_buf, write_queue)


def decode_loop(SharedMemoryBuffer sm_buf, BinaryRingBuffer read_queue):
    with nogil:
        _decode_loop(sm_buf, read_queue)
