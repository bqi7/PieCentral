# distutils: language = c++

"""
Smart Sensor messaging and parsing.

This module implements the Hibike protocol at the byte-level.
"""

from runtime.packet cimport RingBuffer
from cython.operator cimport dereference as deref
from libcpp.string cimport string


cdef class BinaryRingBuffer:
    DEFAULT_CAPACITY = 16 * 1024
    cdef RingBuffer *buf

    def __cinit__(self, size_t capacity = DEFAULT_CAPACITY):
        self.buf = new RingBuffer(capacity)

    def __dealloc__(self):
        del self.buf

    def __len__(self):
        return self.buf.size()

    def __getitem__(self, Py_ssize_t index):
        return deref(self.buf)[index]

    cpdef extend(self, string buf):
        self.buf.extend(buf)
