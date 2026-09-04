#include "OboeAudioRecorder.hpp"
#include <android/log.h>
#include <vector>

#define LOG_TAG "OboeAudioRecorder"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

OboeAudioRecorder::OboeAudioRecorder(std::shared_ptr<AudioRingBuffer> ringBuffer)
    : m_ringBuffer(std::move(ringBuffer)) {}

OboeAudioRecorder::~OboeAudioRecorder() {
    stopRecording();
}

bool OboeAudioRecorder::startRecording() {
    if (m_isRecording) return true;

    oboe::AudioStreamBuilder builder;
    builder.setDirection(oboe::Direction::Input)
        ->setPerformanceMode(oboe::PerformanceMode::None)
        ->setSharingMode(oboe::SharingMode::Shared)
        ->setFormat(oboe::AudioFormat::I16) // I16 for 100% Android hardware & emulator microphone compatibility
        ->setChannelCount(kChannelCount)
        ->setSampleRate(kSampleRate)
        ->setDataCallback(this);

    oboe::Result result = builder.openStream(m_stream);
    if (result != oboe::Result::OK) {
        LOGE("Failed to open Oboe audio recording stream. Error: %s", oboe::convertToText(result));
        return false;
    }

    result = m_stream->requestStart();
    if (result != oboe::Result::OK) {
        LOGE("Failed to start Oboe audio stream. Error: %s", oboe::convertToText(result));
        m_stream->close();
        return false;
    }

    m_isRecording = true;
    LOGI("Oboe audio recording stream started successfully at 16kHz Mono.");
    return true;
}

void OboeAudioRecorder::stopRecording() {
    if (!m_isRecording || !m_stream) return;

    try {
        m_stream->requestStop();
        m_stream->close();
        m_stream.reset();
    } catch (...) {
        LOGE("Exception while stopping Oboe audio stream");
    }
    m_isRecording = false;
    LOGI("Oboe audio recording stream stopped.");
}

oboe::DataCallbackResult OboeAudioRecorder::onAudioReady(
    oboe::AudioStream *audioStream,
    void *audioData,
    int32_t numFrames
) {
    if (!audioData || numFrames <= 0) {
        return oboe::DataCallbackResult::Continue;
    }

    if (m_ringBuffer) {
        std::vector<float> floatBuffer(numFrames);

        if (audioStream->getFormat() == oboe::AudioFormat::I16) {
            const int16_t *intData = static_cast<const int16_t *>(audioData);
            for (int32_t i = 0; i < numFrames; ++i) {
                floatBuffer[i] = intData[i] / 32768.0f; // Convert 16-bit PCM int to normalized float [-1.0, 1.0]
            }
        } else if (audioStream->getFormat() == oboe::AudioFormat::Float) {
            const float *floatData = static_cast<const float *>(audioData);
            for (int32_t i = 0; i < numFrames; ++i) {
                floatBuffer[i] = floatData[i];
            }
        }

        m_ringBuffer->write(floatBuffer.data(), static_cast<size_t>(numFrames));
    }

    return oboe::DataCallbackResult::Continue;
}
