#include <chrono>
#include <deque>
#include <mutex>
#include <condition_variable>
#include "ringbuffer.h"

#define DEFAULT_TIMEOUT 100000  // 10^5 us = 0.1s

namespace ringbuffer {
    RingBuffer::RingBuffer(size_t capacity) {
        this->data = (uint8_t *) malloc(capacity * sizeof(uint8_t));
        this->start = this->end = 0;
        this->capacity = capacity;
    }

    RingBuffer::~RingBuffer() {
        free(this->data);
    }

    size_t RingBuffer::size_range(size_t start, size_t end) {
        if (start <= end)
            return end - start;
        return end + (this->capacity - start);
    }

    size_t RingBuffer::size(void) {
        std::lock_guard<std::recursive_mutex> guard(this->lock);
        return this->size_range(this->start, this->end);
    }

    inline size_t RingBuffer::wrap_index(size_t base, size_t pos) {
        return (base + pos) % this->capacity;
    }

    uint8_t RingBuffer::operator[](size_t pos) {
        std::lock_guard<std::recursive_mutex> guard(this->lock);
        if (pos < this->size())
            return this->data[this->wrap_index(this->start, pos)];
        throw std::out_of_range("RingBuffer: Accessing out-of-bounds index.");
    }

    void RingBuffer::extend(std::string str) {
        {
            std::lock_guard<std::recursive_mutex> guard(this->lock);
            size_t new_size = this->size() + str.size();
            if (new_size >= this->capacity) {
                throw std::out_of_range("RingBuffer: Extending would exceed capacity.");
            }
            for (size_t pos = 0; pos < str.size(); pos++) {
                size_t buf_pos = this->wrap_index(this->end, pos);
                this->data[buf_pos] = str[pos];
                if (str[pos] == '\0')
                    this->delimeters.push_back(buf_pos);
            }
            this->end = this->wrap_index(this->end, str.size());
        }
        if (!this->delimeters.empty())
            data_ready.notify_one();
    }

    std::string RingBuffer::read(void) {
        std::unique_lock<std::recursive_mutex> locked(this->lock);
        std::chrono::microseconds timeout(DEFAULT_TIMEOUT);
        bool ready = this->data_ready.wait_for(locked, timeout, [this] {
            return !this->delimeters.empty();
        });
        if (!ready) {
            throw std::runtime_error("RingBuffer: Read timed out.");
        }

        size_t next_delimeter = this->delimeters.front();
        this->delimeters.pop_front();
        size_t packet_len = this->size_range(this->start, next_delimeter);
        std::string str;
        str.resize(packet_len);
        for (size_t pos = 0; pos < packet_len; pos++) {
            str.at(pos) = this->data[this->wrap_index(this->start, pos)];
        }
        this->start = this->wrap_index(this->start, packet_len + 1);

        this->lock.unlock();
        return str;
    }
}
