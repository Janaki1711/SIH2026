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

# Source files for Member 1 (Chhavi) Audio STT Core
set(AUDIO_STT_SOURCES
    NativeSTTBridge.cpp
    native_bridge.cpp
    OboeAudioRecorder.cpp
    SileroVAD.cpp
    IndicSTTEngine.cpp
)

# Build Shared Library libaudio_stt_core.so
add_library(
    audio_stt_core
    SHARED
    ${AUDIO_STT_SOURCES}
)

# Link Libraries
target_link_libraries(
    audio_stt_core
    oboe::oboe
    onnxruntime
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

