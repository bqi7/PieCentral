from libcpp.string cimport string


cdef extern from "_messaging.cpp":
    pass


cdef extern from "_messaging.cpp" namespace "messaging":
    cpdef string cobs_encode(string) nogil
    cpdef string cobs_decode(string) nogil
