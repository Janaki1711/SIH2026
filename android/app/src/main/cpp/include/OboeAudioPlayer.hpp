#pragma once

#include <oboe/Oboe.h>
#include <memory>
#include "AudioRingBuffer.hpp"

class OboeAudioPlayer : public oboe::AudioStreamDataCallback, public oboe::AudioStreamErrorCallback {
public:
    OboeAudioPlayer();
    ~OboeAudioPlayer() override;

    bool start(int32_t sampleRate = 16000, int32_t channelCount = 1);
    void stop();
    void pause();
    void flush();

    size_t enqueueAudio(const float* pcmData, size_t sampleCount);
    void setVolume(float volume);

    oboe::DataCallbackResult onAudioReady(
        oboe::AudioStream* audioStream,
        void* audioData,
        int32_t numFrames) override;

    void onErrorAfterClose(oboe::AudioStream* stream, oboe::Result error) override;

private:
    std::shared_ptr<oboe::AudioStream> stream_;
    std::unique_ptr<AudioRingBuffer> ringBuffer_;
    std::atomic<float> volume_{1.0f};
    std::atomic<bool> isPlaying_{false};
};
