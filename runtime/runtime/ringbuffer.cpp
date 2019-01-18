#include <mutex>
#include <condition_variable>
#include "ringbuffer.h"

#define NO_DELIMETER (-1)

namespace ringbuffer {
    RingBuffer::RingBuffer(uint8_t *data, size_t capacity) {
        this->data = data;
        this->start = this->end = 0;
        this->capacity = capacity;
        this->next_delimeter = NO_DELIMETER;
    }

    size_t RingBuffer::size_up_to_index(size_t index) {
        if (this->start <= index)
            return index - this->start;
        return index + (this->capacity - this->start);
    }

    size_t RingBuffer::size(void) {
        std::lock_guard<std::recursive_mutex> guard(this->lock);
        return this->size_up_to_index(this->end);
    };

    inline size_t RingBuffer::wrap_index(size_t pos) {
        return (this->start + pos) % this->capacity;
    }

    uint8_t RingBuffer::operator[](size_t pos) {
        std::lock_guard<std::recursive_mutex> guard(this->lock);
        if (pos < this->size())
            return this->data[this->wrap_index(pos)];
        throw std::out_of_range("RingBuffer: Accessing out-of-bounds index.");
    };

    void RingBuffer::extend(std::string str) {
        {
            std::lock_guard<std::recursive_mutex> guard(this->lock);
            if (this->size() + str.size() >= this->capacity) {
                throw std::out_of_range("RingBuffer: Extending would exceed capacity.");
            }
            for (size_t pos = 0; pos < str.size(); pos++) {
                size_t buf_pos = this->wrap_index(pos);
                this->data[buf_pos] = str[pos];
                if (this->next_delimeter == NO_DELIMETER && str[pos] == '\0')
                    this->next_delimeter = buf_pos;
            }
            this->end = this->wrap_index(str.size());
        }
        if (this->next_delimeter != NO_DELIMETER)
            data_ready.notify_one();
    }

    std::string RingBuffer::read(void) {
        std::unique_lock<std::recursive_mutex> locked(this->lock);
        this->data_ready.wait(locked, [this] {
            return this->next_delimeter != NO_DELIMETER;
        });

        size_t packet_len = this->size_up_to_index(this->next_delimeter);
        std::string str;
        str.resize(packet_len);
        for (size_t pos = 0; pos < packet_len; pos++) {
            str.at(pos) = this->data[this->wrap_index(pos)];
        }
        this->start = this->wrap_index(packet_len + 1);

        this->lock.unlock();
        return str;
    }
}
