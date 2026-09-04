#pragma once

#include <vector>
#include <atomic>
#include <cstddef>
#include <algorithm>
#include <cstring>

class AudioRingBuffer {
public:
    explicit AudioRingBuffer(size_t capacity = 16384)
        : buffer_(capacity), capacity_(capacity), head_(0), tail_(0) {}

    void reset() {
        head_.store(0, std::memory_order_relaxed);
        tail_.store(0, std::memory_order_relaxed);
    }

    size_t write(const float* data, size_t count) {
        size_t written = 0;
        size_t current_tail = tail_.load(std::memory_order_relaxed);
        size_t current_head = head_.load(std::memory_order_acquire);

        size_t available = capacity_ - (current_tail - current_head);
        size_t to_write = std::min(count, available);

        for (size_t i = 0; i < to_write; ++i) {
            buffer_[(current_tail + i) % capacity_] = data[i];
        }

        tail_.store(current_tail + to_write, std::memory_order_release);
        return to_write;
    }

    size_t read(float* data, size_t count) {
        size_t current_head = head_.load(std::memory_order_relaxed);
        size_t current_tail = tail_.load(std::memory_order_acquire);

        size_t available = current_tail - current_head;
        size_t to_read = std::min(count, available);

        for (size_t i = 0; i < to_read; ++i) {
            data[i] = buffer_[(current_head + i) % capacity_];
        }

        head_.store(current_head + to_read, std::memory_order_release);
        return to_read;
    }

    size_t availableRead() const {
        size_t current_head = head_.load(std::memory_order_relaxed);
        size_t current_tail = tail_.load(std::memory_order_relaxed);
        return current_tail - current_head;
    }

    size_t getCapacity() const {
        return capacity_;
    }

private:
    std::vector<float> buffer_;
    size_t capacity_;
    std::atomic<size_t> head_;
    std::atomic<size_t> tail_;
};
