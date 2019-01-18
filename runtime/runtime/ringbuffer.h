#ifndef RINGBUFFER_H
#define RINGBUFFER_H

namespace ringbuffer {
    class RingBuffer {
    private:
        size_t capacity, start, end;
        uint8_t *data;
        std::recursive_mutex lock;
        std::condition_variable data_ready;
    public:
        RingBuffer();
        RingBuffer(size_t);
        ~RingBuffer();
        size_t size();
        uint8_t operator[](size_t);
        void extend(std::string);
    };
}

#endif
