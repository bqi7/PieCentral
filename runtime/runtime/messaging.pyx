# distutils: language = c++

"""
Runtime module for encoding and decoding Smart Sensor messages.
"""

from libc.stdint cimport uint8_t, uint16_t, uint64_t
from libcpp.string cimport string
from runtime.buffer cimport SensorBuffer, BinaryRingBuffer


cpdef enum MessageType:
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


cpdef uint8_t compute_checksum(string message) nogil:
    cdef uint8_t checksum = 0
    for i in range(message.size()):
        checksum ^= message[i]
    return checksum


cpdef string build_packet(MessageType type_id, string payload) nogil:
    cdef size_t payload_len = payload.size()
    cdef string message
    if type_id > 0xFF or payload_len > 0xFF:
        return message
    message += (<uint8_t> type_id)
    message += (<uint8_t> payload_len)
    message += payload
    message += compute_checksum(message)
    return message


# cpdef string make_ping() nogil:
#     cdef string empty
#     return build_packet(MessageType.PING, empty)
#
#
# cdef string make_sub_req() nogil:
#     pass
#
#
# cdef string make_read() nogil:
#     pass
#
#
# cdef string make_write() nogil:
#     pass
#
#
# cdef string make_heartbeat() nogil:
#     pass


# cpdef string parse_packet()


cdef void _encode_loop(SensorBuffer buf, BinaryRingBuffer write_queue) nogil:
    while True:
        # decoded_packet = build_packet()
        # write_queue.extend()
        pass


cdef void _decode_loop(SensorBuffer buf, BinaryRingBuffer read_queue) nogil:
    while True:
        packet = read_queue.read()
        packet = cobs_decode(packet)
        if packet.size() < 3:
            continue
        checksum = compute_checksum(packet.substr(0, packet.size() - 1))
        if checksum != packet.at(packet.size() - 1):
            continue


def encode_loop(SensorBuffer buf not None, BinaryRingBuffer write_queue not None):
    with nogil:
        _encode_loop(buf, write_queue)


def decode_loop(SensorBuffer buf not None, BinaryRingBuffer read_queue not None):
    # with nogil:
        _decode_loop(buf, read_queue)
