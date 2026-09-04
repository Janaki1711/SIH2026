#include "Member3Integration.hpp"
#include <chrono>
#include <cstring>
#include <iostream>

namespace itantra::integration {

Member3Engine::Member3Engine() {}

EncodedSemanticPacket Member3Engine::processTranscript(
    const std::string& transcript,
    const std::string& sourceLanguage,
    const std::string& targetLanguage,
    const std::vector<uint8_t>& prosodyVector,
    const std::string& callsign,
    uint32_t sequence,
    int32_t priority
) {
    auto tStart = std::chrono::high_resolution_clock::now();

    EncodedSemanticPacket out;
    out.sourceLanguage = sourceLanguage.empty() ? "en" : sourceLanguage;
    out.targetLanguage = targetLanguage.empty() ? "en" : targetLanguage;
    out.sequenceNumber = sequence;

    // 1. Semantic Analysis via Multi-Task TinyML Agent
    auto tInferStart = std::chrono::high_resolution_clock::now();
    out.semanticResult = agent_.analyze(transcript, out.sourceLanguage, prosodyVector);
    auto tInferEnd = std::chrono::high_resolution_clock::now();

    out.compressionTier = out.semanticResult.compressionTier;

    // Map priority if not explicitly specified
    if (priority < 0) {
        if (out.semanticResult.urgency == semantic::UrgencyCode::CRITICAL_SOS) {
            out.priority = static_cast<uint32_t>(protocol::PriorityLevel::LIFE_SAFETY_ALERT);
        } else if (out.semanticResult.urgency == semantic::UrgencyCode::TACTICAL) {
            out.priority = static_cast<uint32_t>(protocol::PriorityLevel::TACTICAL);
        } else {
            out.priority = static_cast<uint32_t>(protocol::PriorityLevel::ROUTINE);
        }
    } else {
        out.priority = static_cast<uint32_t>(priority);
    }

    // 2. 3-Tier Semantic Compression
    std::vector<uint8_t> compressedPayload = semantic::SemanticCompressor::compress(out.semanticResult);
    out.payloadSize = compressedPayload.size();

    // 3. Protobuf Framing & CRC16-CCITT Checksum
    auto tFrameStart = std::chrono::high_resolution_clock::now();
    out.serializedBytes = protocol::PacketFramer::framePacket(
        compressedPayload,
        out.semanticResult.detectedLanguage,
        callsign,
        sequence,
        out.priority,
        out.semanticResult.prosodyVector
    );
    auto tFrameEnd = std::chrono::high_resolution_clock::now();

    auto tEnd = std::chrono::high_resolution_clock::now();

    // 4. Calculate Authentic Telemetry Metrics
    out.telemetry.originalTextBytes = transcript.size();
    out.telemetry.compressedPayloadBytes = out.payloadSize;
    out.telemetry.totalWireBytes = out.serializedBytes.size();
    if (out.payloadSize > 0) {
        out.telemetry.compressionRatio = static_cast<float>(transcript.size()) / static_cast<float>(out.payloadSize);
    } else {
        out.telemetry.compressionRatio = 1.0f;
    }
    out.telemetry.semanticInferenceTimeMs = std::chrono::duration<float, std::milli>(tInferEnd - tInferStart).count();
    out.telemetry.framingTimeMs = std::chrono::duration<float, std::milli>(tFrameEnd - tFrameStart).count();
    out.telemetry.totalProcessingTimeMs = std::chrono::duration<float, std::milli>(tEnd - tStart).count();
    out.telemetry.confidence = out.semanticResult.confidence;
    out.telemetry.fallbackUsed = out.semanticResult.isFallback;

    return out;
}

DecodedSemanticMessage Member3Engine::decodePacket(
    const std::vector<uint8_t>& wireBytes,
    const std::string& targetLanguage
) {
    auto tStart = std::chrono::high_resolution_clock::now();
    DecodedSemanticMessage msg;
    msg.targetLanguage = targetLanguage.empty() ? "en" : targetLanguage;

    // 1. Protobuf Deserialization & CRC16-CCITT Verification
    protocol::VoicePacket packet = protocol::PacketFramer::parseAndValidateFrame(wireBytes);
    msg.crcValid = true;
    msg.sourceLanguage = packet.source_language();
    msg.priority = static_cast<uint32_t>(packet.priority());

    // Recover Prosody Vector
    if (!packet.prosody_vector().empty()) {
        const std::string& pVec = packet.prosody_vector();
        msg.prosodyVector.assign(pVec.begin(), pVec.end());
    }

    // 2. Semantic Decompression (Tier 1/2/3)
    const std::string& payloadStr = packet.compressed_payload();
    std::vector<uint8_t> payloadBytes(payloadStr.begin(), payloadStr.end());
    semantic::SemanticResult semRes = semantic::SemanticCompressor::decompress(payloadBytes);

    msg.intent = semRes.intent;
    msg.action = semRes.action;
    msg.hazard = semRes.hazard;
    msg.urgency = semRes.urgency;
    msg.location = semRes.location;
    msg.personCount = semRes.personCount;
    msg.confidence = semRes.confidence;

    // 3. Translation Realization in Target Language
    msg.decodedText = translator_.realize(semRes, msg.targetLanguage);

    auto tEnd = std::chrono::high_resolution_clock::now();
    msg.decodeTimeMs = std::chrono::duration<float, std::milli>(tEnd - tStart).count();

    return msg;
}

// ─────────────────────────────────────────────────────────────────────────────
// C / JNI Readiness Exports
// ─────────────────────────────────────────────────────────────────────────────
extern "C" {

int nativeProcessTinyML(
    const char* transcript,
    const char* sourceLang,
    const char* targetLang,
    const uint8_t* prosody16,
    const char* callsign,
    uint32_t sequence,
    uint8_t* outBuffer,
    int maxOutBufferSize
) {
    if (!transcript || !outBuffer || maxOutBufferSize <= 0) return -1;
    try {
        static Member3Engine engine;
        std::vector<uint8_t> prosodyVec;
        if (prosody16) {
            prosodyVec.assign(prosody16, prosody16 + 16);
        }
        auto packet = engine.processTranscript(
            transcript,
            sourceLang ? sourceLang : "en",
            targetLang ? targetLang : "en",
            prosodyVec,
            callsign ? callsign : "CMD_ALPHA",
            sequence
        );
        if (packet.serializedBytes.size() > static_cast<size_t>(maxOutBufferSize)) {
            return -2; // Buffer too small
        }
        std::memcpy(outBuffer, packet.serializedBytes.data(), packet.serializedBytes.size());
        return static_cast<int>(packet.serializedBytes.size());
    } catch (...) {
        return -3;
    }
}

int nativeDecodePacket(
    const uint8_t* wireBytes,
    int wireBytesLength,
    const char* targetLang,
    char* outTextBuffer,
    int maxOutTextSize,
    uint8_t* outProsody16
) {
    if (!wireBytes || wireBytesLength <= 0 || !outTextBuffer || maxOutTextSize <= 0) return -1;
    try {
        static Member3Engine engine;
        std::vector<uint8_t> data(wireBytes, wireBytes + wireBytesLength);
        auto decoded = engine.decodePacket(data, targetLang ? targetLang : "en");
        
        size_t textLen = decoded.decodedText.size();
        if (textLen >= static_cast<size_t>(maxOutTextSize)) {
            textLen = maxOutTextSize - 1;
        }
        std::memcpy(outTextBuffer, decoded.decodedText.c_str(), textLen);
        outTextBuffer[textLen] = '\0';

        if (outProsody16) {
            if (decoded.prosodyVector.size() >= 16) {
                std::memcpy(outProsody16, decoded.prosodyVector.data(), 16);
            } else {
                std::memset(outProsody16, 0, 16);
            }
        }
        return static_cast<int>(textLen);
    } catch (...) {
        return -3;
    }
}

} // extern "C"

} // namespace itantra::integration
