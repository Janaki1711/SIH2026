#include <jni.h>
#include <string>

extern "C" JNIEXPORT jint JNICALL
Java_org_isro_itantra_native_NativeBridge_processBuffer(
        JNIEnv* env,
        jobject /* this */,
        jobject buffer,
        jint size) {
    
    if (buffer == nullptr) {
        return -1;
    }

    // Access the DirectByteBuffer without copying
    auto* data = static_cast<jbyte*>(env->GetDirectBufferAddress(buffer));
    
    if (data == nullptr) {
        // Not a direct buffer
        return -2;
    }

    jlong capacity = env->GetDirectBufferCapacity(buffer);
    if (size > capacity) {
        return -3; // Invalid size
    }

    // Compute a simple checksum to prove we read the data correctly
    jint checksum = 0;
    for (int i = 0; i < size; ++i) {
        checksum += data[i];
    }

    // We can also modify the buffer in-place to prove two-way communication
    if (size > 0) {
        data[0] = 42; // arbitrary modification
    }

    return checksum;
}

#include "OboeAudioRecorder.hpp"
#include "AudioRingBuffer.hpp"
#include <memory>

static std::shared_ptr<AudioRingBuffer> g_ringBuffer;
static std::unique_ptr<OboeAudioRecorder> g_oboeRecorder;

std::shared_ptr<AudioRingBuffer> getGlobalRingBuffer() {
    return g_ringBuffer;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_org_isro_itantra_native_NativeBridge_startOboeRecording(JNIEnv* env, jobject /* this */) {
    if (!g_ringBuffer) {
        g_ringBuffer = std::make_shared<AudioRingBuffer>(16000 * 60); // 60 seconds buffer
    }
    g_ringBuffer->reset();
    
    if (!g_oboeRecorder) {
        g_oboeRecorder = std::make_unique<OboeAudioRecorder>(g_ringBuffer);
    }
    
    return g_oboeRecorder->startRecording() ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT void JNICALL
Java_org_isro_itantra_native_NativeBridge_stopOboeRecording(JNIEnv* env, jobject /* this */) {
    if (g_oboeRecorder) {
        g_oboeRecorder->stopRecording();
    }
}

