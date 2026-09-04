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
