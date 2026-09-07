#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include "SemanticCodebook.hpp"
#include "TinyMLAgent.hpp"
#include "SemanticCompressor.hpp"
#include "PacketFramer.hpp"
#include "TranslationBridge.hpp"

namespace itantra::integration {

struct PacketTelemetry {
    size_t originalTextBytes = 0;
    size_t compressedPayloadBytes = 0;
    size_t totalWireBytes = 0;
    float compressionRatio = 1.0f;
    float semanticInferenceTimeMs = 0.0f;
    float translationTimeMs = 0.0f;
    float framingTimeMs = 0.0f;
    float totalProcessingTimeMs = 0.0f;
    float confidence = 1.0f;
    bool fallbackUsed = false;
};

struct EncodedSemanticPacket {
    std::vector<uint8_t> serializedBytes;
    semantic::CompressionTier compressionTier = semantic::CompressionTier::TIER_1_MACRO;
    size_t payloadSize = 0;
    semantic::SemanticResult semanticResult;
    uint32_t priority = 0;
    std::string sourceLanguage;
    std::string targetLanguage;
    uint32_t sequenceNumber = 0;
    PacketTelemetry telemetry;
};

struct DecodedSemanticMessage {
    std::string decodedText;
    std::string sourceLanguage;
    std::string targetLanguage;
    uint32_t priority = 0;
    semantic::UrgencyCode urgency = semantic::UrgencyCode::ROUTINE;
    semantic::LocationEntity location;
    semantic::ActionCode intent = semantic::ActionCode::UNKNOWN;
    semantic::ActionCode action = semantic::ActionCode::UNKNOWN;
    semantic::HazardCode hazard = semantic::HazardCode::NONE;
    uint32_t personCount = 0;
    std::vector<uint8_t> prosodyVector;
    bool crcValid = false;
    float confidence = 1.0f;
    float decodeTimeMs = 0.0f;
};

class Member3Engine {
public:
    Member3Engine();

    /// Top-level Sender API: Takes an STT transcript and produces network-ready bytes
    /// @param transcript STT natural language text
    /// @param sourceLanguage Source BCP-47 language ("hi", "kn", "ta", "mr", "en")
    /// @param targetLanguage Target BCP-47 language for receiver realization
    /// @param prosodyVector Optional 16-byte prosody vector from audio subsystem
    /// @param callsign Operator callsign (e.g. "RESCUE_01")
    /// @param sequence Monotonically increasing packet counter
    /// @param priority 0=ROUTINE, 1=TACTICAL, 2=LIFE_SAFETY_ALERT (if -1, auto-inferred from urgency)
    /// @return EncodedSemanticPacket containing serialized wire bytes and full telemetry
    EncodedSemanticPacket processTranscript(
        const std::string& transcript,
        const std::string& sourceLanguage = "en",
        const std::string& targetLanguage = "en",
        const std::vector<uint8_t>& prosodyVector = {},
        const std::string& callsign = "CMD_ALPHA",
        uint32_t sequence = 1,
        int32_t priority = -1
    );

    /// Top-level Receiver API: Takes network wire bytes and produces TTS-ready output
    /// @param wireBytes Raw network bytes received from M4 wireless transport
    /// @param targetLanguage Language for realization / translation (e.g. "hi", "kn", "ta", "en")
    /// @return DecodedSemanticMessage containing realized text and 16-byte prosody vector
    DecodedSemanticMessage decodePacket(
        const std::vector<uint8_t>& wireBytes,
        const std::string& targetLanguage = "en"
    );

    /// Expose sub-components
    semantic::TinyMLAgent& getTinyMLAgent() { return agent_; }
    translation::TranslationBridge& getTranslationBridge() { return translator_; }

private:
    semantic::TinyMLAgent agent_;
    translation::TranslationBridge translator_;
};

// ─────────────────────────────────────────────────────────────────────────────
// C-Style / JNI Readiness Exports for Android (Member 5 Integration)
// ─────────────────────────────────────────────────────────────────────────────
extern "C" {
    /// JNI entry point: Process transcript and frame into binary buffer
    int nativeProcessTinyML(
        const char* transcript,
        const char* sourceLang,
        const char* targetLang,
        const uint8_t* prosody16,
        const char* callsign,
        uint32_t sequence,
        uint8_t* outBuffer,
        int maxOutBufferSize
    );

    /// JNI entry point: Decode binary buffer and realize text
    int nativeDecodePacket(
        const uint8_t* wireBytes,
        int wireBytesLength,
        const char* targetLang,
        char* outTextBuffer,
        int maxOutTextSize,
        uint8_t* outProsody16
    );
}

} // namespace itantra::integration
