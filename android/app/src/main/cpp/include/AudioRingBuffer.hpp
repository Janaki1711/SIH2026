#pragma once

#include <vector>
#include <atomic>
#include <cstddef>
#include <cstring>

/**
 * @brief Lock-Free Circular Ring Buffer for streaming 16kHz Mono Float PCM audio.
 * Designed for low-latency thread safety between the Oboe Audio Callback (Writer)
 * and the Silero VAD / STT Processing Thread (Reader).
 */
class AudioRingBuffer {
public:
    explicit AudioRingBuffer(size_t capacity = 16000 * 10) // Default 10 seconds capacity
        : m_capacity(capacity),
          m_buffer(capacity, 0.0f),
          m_write_index(0),
          m_read_index(0) {}

    ~AudioRingBuffer() = default;

    /**
     * @brief Writes PCM float samples to the buffer (Non-blocking, called by Oboe thread).
     * @param data Pointer to input float samples [-1.0, 1.0].
     * @param count Number of samples to write (e.g., 480 samples for 30ms).
     * @return true if successfully written, false if buffer overflow occurs.
     */
    bool write(const float* data, size_t count) {
        if (!data || count == 0) return false;

        const size_t current_write = m_write_index.load(std::memory_order_relaxed);
        const size_t current_read = m_read_index.load(std::memory_order_acquire);

        // Check for overflow
        if (m_capacity - (current_write - current_read) < count) {
            return false; // Overflow: Reader thread is behind
        }

        for (size_t i = 0; i < count; ++i) {
            m_buffer[(current_write + i) % m_capacity] = data[i];
        }

        m_write_index.store(current_write + count, std::memory_order_release);
        return true;
    }

    /**
     * @brief Reads PCM float samples from the buffer (Non-blocking, called by VAD thread).
     * @param dest Output buffer destination.
     * @param count Number of samples to read (e.g., 512 samples for Silero VAD).
     * @return true if successfully read, false if not enough samples available.
     */
    bool read(float* dest, size_t count) {
        if (!dest || count == 0) return false;

        const size_t current_write = m_write_index.load(std::memory_order_acquire);
        const size_t current_read = m_read_index.load(std::memory_order_relaxed);

        // Check if enough data is available
        if (current_write - current_read < count) {
            return false; // Underflow: Not enough samples ready
        }

        for (size_t i = 0; i < count; ++i) {
            dest[i] = m_buffer[(current_read + i) % m_capacity];
        }

        m_read_index.store(current_read + count, std::memory_order_release);
        return true;
    }

    /**
     * @brief Returns the total number of unread audio samples currently in the buffer.
     */
    size_t available() const {
        const size_t current_write = m_write_index.load(std::memory_order_acquire);
        const size_t current_read = m_read_index.load(std::memory_order_relaxed);
        return (current_write >= current_read) ? (current_write - current_read) : 0;
    }

    /**
     * @brief Resets the ring buffer pointers.
     */
    void reset() {
        m_write_index.store(0, std::memory_order_relaxed);
        m_read_index.store(0, std::memory_order_relaxed);
    }

private:
    size_t m_capacity;
    std::vector<float> m_buffer;
    std::atomic<size_t> m_write_index;
    std::atomic<size_t> m_read_index;
};
