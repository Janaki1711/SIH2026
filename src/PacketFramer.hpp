#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include "packet_schema.pb.h"
#include "SemanticCodebook.hpp"
#include "TinyMLAgent.hpp"

namespace itantra::protocol {

class PacketFramer {
public:
    static constexpr uint32_t MAGIC_HEADER = 0x41475931; // "AGY1"

    /// Calculate CRC16-CCITT (polynomial 0x1021, init 0xFFFF)
    static uint16_t calculateCRC16(const uint8_t* data, size_t length);
    static uint16_t calculateCRC16(const std::vector<uint8_t>& data);

    /// Frame a semantic payload into a network-ready Protobuf byte buffer.
    /// @param compressedPayload The 3-tier compressed payload bytes
    /// @param sourceLanguage BCP-47 language tag ("hi", "kn", "ta", "en", etc.)
    /// @param callsign Operator callsign ("RESCUE_01")
    /// @param sequence Monotonically increasing sequence number
    /// @param priority Triage priority level (0=ROUTINE, 1=TACTICAL, 2=LIFE_SAFETY_ALERT)
    /// @param prosodyVector Optional 16-byte prosody vector
    /// @return Serialized Protobuf frame
    static std::vector<uint8_t> framePacket(
        const std::vector<uint8_t>& compressedPayload,
        const std::string& sourceLanguage,
        const std::string& callsign,
        uint32_t sequence,
        uint32_t priority,
        const std::vector<uint8_t>& prosodyVector = {}
    );

    /// Validate frame CRC and parse Protobuf VoicePacket.
    /// @param wireBytes Raw network bytes received
    /// @return Decoded VoicePacket
    /// @throws std::runtime_error on CRC mismatch, wrong magic header, or parse failure
    static VoicePacket parseAndValidateFrame(const std::vector<uint8_t>& wireBytes);

    /// Helper to validate if frame bytes are intact without throwing
    static bool validateFrame(const std::vector<uint8_t>& wireBytes);
};

} // namespace itantra::protocol
