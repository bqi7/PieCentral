#include <mutex>
#include <condition_variable>
#include "ringbuffer.h"

namespace ringbuffer {
    RingBuffer::RingBuffer() {}
    RingBuffer::RingBuffer(size_t capacity) {}
    RingBuffer::~RingBuffer() {}
    size_t RingBuffer::size() { return 0; };
    uint8_t RingBuffer::operator[](size_t pos) { return '\0'; } ;
    void RingBuffer::extend(std::string str) {}
}
