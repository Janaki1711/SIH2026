cmake_minimum_required(VERSION 3.22.1)
project("audio_stt_core")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include header directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Android Log Library
find_library(log-lib log)

# Google Oboe (Native Prefab package)
find_package(oboe REQUIRED CONFIG)

# Import ONNX Runtime Shared Library with IMPORTED_NO_SONAME
add_library(onnxruntime SHARED IMPORTED)
set_target_properties(onnxruntime PROPERTIES
    IMPORTED_LOCATION "${CMAKE_CURRENT_SOURCE_DIR}/../jniLibs/${ANDROID_ABI}/libonnxruntime.so"
    IMPORTED_NO_SONAME TRUE
)

# --- whisper.cpp (gate-passed STT for te/ta/kn/ml) ---
# Pinned to the exact commit the CER gate was run against
# (/tmp/opencode/sttlab/RESULTS.md: avg CER 0.169 vs conformer 0.368).
# GGML CPU backend only; no examples/tests/server needed on-device.
include(FetchContent)
set(WHISPER_BUILD_TESTS    OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(WHISPER_BUILD_SERVER   OFF CACHE BOOL "" FORCE)
set(WHISPER_STANDALONE     OFF CACHE BOOL "" FORCE)
set(WHISPER_ALL_WARNINGS   OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    whispercpp
    GIT_REPOSITORY https://github.com/ggerganov/whisper.cpp.git
    GIT_TAG        d09f61a708f3487afa956ff578e60eae5e7a233c
)
FetchContent_MakeAvailable(whispercpp)

# AGP builds the debug variant with CMAKE_BUILD_TYPE=Debug, which the NDK
# compiles at -O0. That made whisper decode take 45 s for 5 s of audio
# (vs 1.5 s optimized on the laptop). Force optimization on the
# compute-heavy targets; the rest of the app may stay debug.
foreach(_perf_target whisper ggml ggml-base ggml-cpu)
    if(TARGET ${_perf_target})
        target_compile_options(${_perf_target} PRIVATE -O2)
    endif()
endforeach()

# Source files for Member 1 (Chhavi) Audio STT Core
set(AUDIO_STT_SOURCES
    NativeSTTBridge.cpp
    native_bridge.cpp
    OboeAudioRecorder.cpp
    SileroVAD.cpp
    IndicSTTEngine.cpp
    WhisperSTTEngine.cpp
)

# Build Shared Library libaudio_stt_core.so
add_library(
    audio_stt_core
    SHARED
    ${AUDIO_STT_SOURCES}
)
# Same -O0 problem: buffer/AGC/UTF-8 guard loops in this lib run on every
# utterance. Optimize them while keeping debug info (-g stays from Debug).
target_compile_options(audio_stt_core PRIVATE -O2)

# Link Libraries
target_link_libraries(
    audio_stt_core
    oboe::oboe
    onnxruntime
    whisper
    ${log-lib}
)

# Source files for Member 2 Audio TTS Core
set(AUDIO_TTS_SOURCES
    OboeAudioPlayer.cpp
    VoiceToneCloner.cpp
    IndicTTSEngine.cpp
    NativeTTSBridge.cpp
)

# Build Shared Library libaudio_tts_core.so
add_library(
    audio_tts_core
    SHARED
    ${AUDIO_TTS_SOURCES}
)

# Link Libraries for TTS
target_link_libraries(
    audio_tts_core
    oboe::oboe
    ${log-lib}
)



# --- Member 3: Semantic Engine (itantra_core) ---
include(FetchContent)
FetchContent_Declare(
    protobuf
    GIT_REPOSITORY https://github.com/protocolbuffers/protobuf.git
    GIT_TAG        v3.21.12
)
set(protobuf_BUILD_TESTS OFF CACHE BOOL "Disable tests" FORCE)
set(protobuf_BUILD_PROTOC_BINARIES OFF CACHE BOOL "Disable protoc" FORCE)
set(protobuf_BUILD_SHARED_LIBS OFF CACHE BOOL "Static build" FORCE)
FetchContent_MakeAvailable(protobuf)

set(ITANTRA_CORE_SRCS
    semantic/semantic_jni_bridge.cpp
    semantic/Member3Integration.cpp
    semantic/SemanticCompressor.cpp
    semantic/SemanticCodebook.cpp
    semantic/TinyMLAgent.cpp
    semantic/GeoResolver.cpp
    semantic/TranslationBridge.cpp
    semantic/PacketFramer.cpp
    semantic/PacketEncoder.cpp
    semantic/PacketDecoder.cpp
    semantic/packet_schema.pb.cc
)

add_library(itantra_core SHARED ${ITANTRA_CORE_SRCS})

target_include_directories(itantra_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/semantic
)

add_dependencies(itantra_core libprotobuf-lite)
target_link_libraries(itantra_core PRIVATE
    ${log-lib}
    libprotobuf-lite
)

