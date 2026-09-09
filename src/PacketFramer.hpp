#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <chrono>
#include <unordered_map>
#include "packet_schema.pb.h"
#include "SemanticCodebook.hpp"
#include "TinyMLAgent.hpp"

namespace itantra::protocol {

class PacketFramer {
public:
    static constexpr uint8_t  COMPACT_MAGIC = 0x53;        // 'S' (Semantic compact binary sync byte)
    static constexpr uint32_t MAGIC_HEADER  = 0x41475931;   // "AGY1" (Protobuf legacy sync word)
    
    // Hard limit constants for <= 38B compliance
    static constexpr size_t   MAX_FRAME_SIZE           = 38;
    static constexpr size_t   UNFRAGMENTED_HEADER_SIZE = 7; // Magic(1) + Flags(1) + Seq(2) + Cid(2) + Len(1)
    static constexpr size_t   FRAGMENTED_HEADER_SIZE   = 9; // Magic(1) + Flags(1) + Seq(2) + Cid(2) + FragIdx(1) + TotalFrags(1) + Len(1)
    static constexpr size_t   CRC_SIZE                 = 2; // CRC16(2)
    static constexpr size_t   MAX_FRAGMENT_PAYLOAD     = 27; // 38 - (9 + 2) = 27 bytes per frame
    static constexpr uint8_t  FLAG_FRAGMENTED          = 0x80; // Bit 7 of flags indicates fragmented frame

    /// Calculate CRC16-CCITT (polynomial 0x1021, init 0xFFFF)
    static uint16_t calculateCRC16(const uint8_t* data, size_t length);
    static uint16_t calculateCRC16(const std::vector<uint8_t>& data);

    /// Language code to BCP-47 tag mapping
    static uint8_t languageToCode(const std::string& lang);
    static std::string codeToLanguage(uint8_t code);

    /// Hash callsign string to 16-bit Station ID
    static uint16_t callsignToId(const std::string& callsign);
    static std::string idToCallsign(uint16_t id);

    /// Frames a payload into one or more <=38B compact binary frames with dynamic fragmentation.
    static std::vector<std::vector<uint8_t>> framePayload(
        const std::vector<uint8_t>& payload,
        const std::string& sourceLanguage,
        const std::string& callsign,
        uint32_t sequence,
        uint32_t priority,
        const std::vector<uint8_t>& prosodyVector = {}
    );

    /// Frame a semantic payload into an ultra-compact binary byte buffer (<=38 bytes).
    static std::vector<uint8_t> framePacket(
        const std::vector<uint8_t>& compressedPayload,
        const std::string& sourceLanguage,
        const std::string& callsign,
        uint32_t sequence,
        uint32_t priority,
        const std::vector<uint8_t>& prosodyVector = {}
    );

    /// Validate frame CRC and parse VoicePacket (supports both Compact Binary and Legacy Protobuf).
    static VoicePacket parseAndValidateFrame(const std::vector<uint8_t>& wireBytes);

    /// Helper to validate if frame bytes are intact without throwing
    static bool validateFrame(const std::vector<uint8_t>& wireBytes);
};

/// Structure representing the result of reassembling fragmented frames
struct ReassemblyResult {
    bool isComplete = false;
    VoicePacket packet;
    uint32_t receivedFragments = 0;
    uint32_t totalFragments = 0;
};

/// Thread-safe Reassembler for collecting and reconstructing fragmented messages
class MessageReassembler {
public:
    ReassemblyResult processFrame(const std::vector<uint8_t>& frameBytes);
    void cleanupOldSessions(uint64_t maxAgeSeconds = 30);

private:
    struct Session {
        uint8_t flags = 0;
        uint16_t sequence = 0;
        uint16_t callsignId = 0;
        uint8_t totalFragments = 0;
        std::unordered_map<uint8_t, std::vector<uint8_t>> fragments;
        std::chrono::steady_clock::time_point lastUpdate;
    };
    std::unordered_map<std::string, Session> sessions_;
};

} // namespace itantra::protocol
