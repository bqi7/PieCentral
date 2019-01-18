from libc.stdint cimport uint8_t, uint16_t, uint64_t
from libcpp.string cimport string


cpdef enum ParameterType:
    BOOL = 0,
    UINT8 = 1,
    UINT16 = 2,
    UINT32 = 3,
    UINT64 = 4,
    INT8 = 5,
    INT16 = 6,
    INT32 = 7,
    INT64 = 8,
    FLOAT = 9,
    # Note: Arduino's `double` type is only four bytes. Do not use this type
    # unless your Smart Sensor is actually producing eight-byte values.
    DOUBLE = 10


cdef inline Py_ssize_t size_of_type(ParameterType param_type):
    if param_type == BOOL or param_type == UINT8 or param_type == INT8:
        return 1
    elif param_type == UINT16 or param_type == INT16:
        return 2
    elif param_type == UINT32 or param_type == INT32 or param_type == FLOAT:
        return 4
    elif param_type == UINT64 or param_type == INT64 or param_type == DOUBLE:
        return 8
    else:
        return -1


cdef struct sensor_uid:
    uint16_t device_type
    uint8_t year
    uint64_t id


# cdef class Parameter:
#     ParameterType type
#     bint read
#     bint write
#     float lower
#     float upper


cdef extern from "ringbuffer.cpp":
    pass


cdef extern from "ringbuffer.cpp" namespace "ringbuffer":
    cdef cppclass RingBuffer:
        RingBuffer(size_t) except +
        size_t size()
        uint8_t operator[](size_t)
        void extend(string)
