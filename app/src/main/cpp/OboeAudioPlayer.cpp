#include "OboeAudioPlayer.hpp"
#include <android/log.h>
#include <algorithm>

#define TAG "iTantra_OboePlayer"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

OboeAudioPlayer::OboeAudioPlayer()
    : ringBuffer_(std::make_unique<AudioRingBuffer>(32768)),
      volume_(1.0f),
      isPlaying_(false) {}

OboeAudioPlayer::~OboeAudioPlayer() {
    stop();
}

bool OboeAudioPlayer::start(int32_t sampleRate, int32_t channelCount) {
    if (isPlaying_.load()) return true;

    oboe::AudioStreamBuilder builder;
    builder.setDirection(oboe::Direction::Output)
           ->setPerformanceMode(oboe::PerformanceMode::LowLatency)
           ->setSharingMode(oboe::SharingMode::Exclusive)
           ->setFormat(oboe::AudioFormat::Float)
           ->setChannelCount(channelCount)
           ->setSampleRate(sampleRate)
           ->setDataCallback(this)
           ->setErrorCallback(this);

    oboe::Result result = builder.openStream(stream_);
    if (result != oboe::Result::OK) {
        LOGE("Failed to open Oboe audio output stream: %s", oboe::convertToText(result));
        return false;
    }

    result = stream_->requestStart();
    if (result != oboe::Result::OK) {
        LOGE("Failed to start Oboe audio stream: %s", oboe::convertToText(result));
        stream_->close();
        stream_.reset();
        return false;
    }

    isPlaying_.store(true);
    LOGI("Oboe Audio Stream successfully started (SampleRate=%d, Channels=%d)", sampleRate, channelCount);
    return true;
}

void OboeAudioPlayer::stop() {
    if (!isPlaying_.load()) return;
    isPlaying_.store(false);

    if (stream_) {
        stream_->stop();
        stream_->close();
        stream_.reset();
    }
    LOGI("Oboe Audio Stream stopped");
}

void OboeAudioPlayer::pause() {
    if (stream_ && isPlaying_.load()) {
        stream_->pause();
    }
}

void OboeAudioPlayer::flush() {
    if (ringBuffer_) {
        ringBuffer_->reset();
    }
}

size_t OboeAudioPlayer::enqueueAudio(const float* pcmData, size_t sampleCount) {
    if (!ringBuffer_) return 0;
    return ringBuffer_->write(pcmData, sampleCount);
}

void OboeAudioPlayer::setVolume(float volume) {
    volume_.store(std::max(0.0f, volume));
}

oboe::DataCallbackResult OboeAudioPlayer::onAudioReady(
    oboe::AudioStream* /*audioStream*/,
    void* audioData,
    int32_t numFrames) {

    float* output = static_cast<float*>(audioData);
    size_t samplesNeeded = static_cast<size_t>(numFrames);
    size_t samplesRead = ringBuffer_->read(output, samplesNeeded);

    float vol = volume_.load();
    for (size_t i = 0; i < samplesRead; ++i) {
        output[i] *= vol;
    }

    if (samplesRead < samplesNeeded) {
        std::fill(output + samplesRead, output + samplesNeeded, 0.0f);
    }

    return oboe::DataCallbackResult::Continue;
}

void OboeAudioPlayer::onErrorAfterClose(oboe::AudioStream* /*stream*/, oboe::Result error) {
    LOGE("Oboe AudioStream error after close: %s", oboe::convertToText(error));
}
