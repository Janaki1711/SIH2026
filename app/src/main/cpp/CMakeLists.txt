cmake_minimum_required(VERSION 3.22.1)
project("audio_tts_core")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

find_library(log-lib log)
find_package(oboe REQUIRED CONFIG)

set(AUDIO_TTS_SOURCES
    OboeAudioPlayer.cpp
    VoiceToneCloner.cpp
    IndicTTSEngine.cpp
    NativeTTSBridge.cpp
)

add_library(
    audio_tts_core
    SHARED
    ${AUDIO_TTS_SOURCES}
)

target_link_libraries(
    audio_tts_core
    oboe::oboe
    ${log-lib}
)
