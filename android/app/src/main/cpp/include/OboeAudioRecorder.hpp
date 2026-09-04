#pragma once

#include <oboe/Oboe.h>
#include <memory>
#include "AudioRingBuffer.hpp"

/**
 * @brief Native Audio Capture Engine utilizing Google Oboe (AAudio / OpenSL ES).
 * Ingests 16kHz Mono Float PCM audio directly from hardware microphone into
 * a lock-free AudioRingBuffer.
 */
class OboeAudioRecorder : public oboe::AudioStreamDataCallback {
public:
    explicit OboeAudioRecorder(std::shared_ptr<AudioRingBuffer> ringBuffer);
    ~OboeAudioRecorder() override;

    /**
     * @brief Starts the low-latency audio recording stream.
     * @return true if stream opened and started successfully.
     */
    bool startRecording();

    /**
     * @brief Stops and closes the audio recording stream.
     */
    void stopRecording();

    /**
     * @brief Checks if the audio recorder is currently active.
     */
    bool isRecording() const { return m_isRecording; }

    /**
     * @brief Oboe Audio Data Callback (Executes on high-priority Real-Time Audio Thread).
     * MUST NOT BLOCK, ALLOCATE MEMORY, OR USE LOCKS.
     */
    oboe::DataCallbackResult onAudioReady(
        oboe::AudioStream *audioStream,
        void *audioData,
        int32_t numFrames
    ) override;

private:
    std::shared_ptr<AudioRingBuffer> m_ringBuffer;
    std::shared_ptr<oboe::AudioStream> m_stream;
    bool m_isRecording{false};

    static constexpr int32_t kSampleRate = 16000; // 16kHz
    static constexpr int32_t kChannelCount = 1;  // Mono
};
