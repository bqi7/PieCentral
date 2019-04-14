from libcpp.string cimport string


cdef extern from "packet.cpp":
    pass


cdef extern from "packet.cpp" namespace "packet":
    cpdef string cobs_encode(string) nogil
    cpdef string cobs_decode(string) nogil
