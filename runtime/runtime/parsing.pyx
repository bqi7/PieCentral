from libc.stdint cimport uint8_t

cdef struct SmartSensorPacket:
    uint8_t message_id
    uint8_t payload_len

# cdef void nogil:
