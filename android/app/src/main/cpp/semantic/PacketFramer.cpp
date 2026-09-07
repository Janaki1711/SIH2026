#include "PacketFramer.hpp"
#include <chrono>
#include <stdexcept>
#include <algorithm>

namespace itantra::protocol {

uint16_t PacketFramer::calculateCRC16(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= static_cast<uint16_t>(data[i]) << 8;
        for (int b = 0; b < 8; ++b) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    return crc;
}

uint16_t PacketFramer::calculateCRC16(const std::vector<uint8_t>& data) {
    return calculateCRC16(data.data(), data.size());
}

std::vector<uint8_t> PacketFramer::framePacket(
    const std::vector<uint8_t>& compressedPayload,
    const std::string& sourceLanguage,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority,
    const std::vector<uint8_t>& prosodyVector
) {
    if (compressedPayload.empty()) {
        throw std::invalid_argument("PacketFramer::framePacket — compressedPayload cannot be empty");
    }

    VoicePacket packet;
    packet.set_magic_header(MAGIC_HEADER);
    packet.set_sequence_number(sequence);

    auto nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    packet.set_timestamp_ms(static_cast<uint64_t>(nowMs));

    if (priority > 2) {
        priority = 0;
    }
    packet.set_priority(static_cast<PriorityLevel>(priority));
    packet.set_source_callsign(callsign.empty() ? "CMD_ALPHA" : callsign);
    packet.set_source_language(sourceLanguage.empty() ? "en" : sourceLanguage);

    packet.set_compressed_payload(
        std::string(reinterpret_cast<const char*>(compressedPayload.data()), compressedPayload.size())
    );

    // Validate and set 16-byte prosody vector
    if (!prosodyVector.empty()) {
        std::vector<uint8_t> validProsody = prosodyVector;
        if (validProsody.size() != 16) {
            validProsody.resize(16, 0);
        }
        packet.set_prosody_vector(
            std::string(reinterpret_cast<const char*>(validProsody.data()), validProsody.size())
        );
    }

    // Step 1: Serialize without CRC to compute checksum
    packet.set_crc16_checksum(0);
    std::string serializedPreCRC;
    if (!packet.SerializeToString(&serializedPreCRC)) {
        throw std::runtime_error("PacketFramer::framePacket — Initial Protobuf serialization failed");
    }

    uint16_t crc = calculateCRC16(reinterpret_cast<const uint8_t*>(serializedPreCRC.data()), serializedPreCRC.size());
    packet.set_crc16_checksum(crc);

    // Step 2: Final serialization with computed CRC16 field
    std::string serializedFinal;
    if (!packet.SerializeToString(&serializedFinal)) {
        throw std::runtime_error("PacketFramer::framePacket — Final Protobuf serialization failed");
    }

    return std::vector<uint8_t>(serializedFinal.begin(), serializedFinal.end());
}

VoicePacket PacketFramer::parseAndValidateFrame(const std::vector<uint8_t>& wireBytes) {
    if (wireBytes.empty()) {
        throw std::invalid_argument("PacketFramer::parseAndValidateFrame — received empty byte buffer");
    }

    VoicePacket packet;
    std::string rawStr(reinterpret_cast<const char*>(wireBytes.data()), wireBytes.size());
    if (!packet.ParseFromString(rawStr)) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — Protobuf deserialization failed");
    }

    if (packet.magic_header() != MAGIC_HEADER) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — Invalid magic header (sync word mismatch)");
    }

    // Validate CRC16
    uint32_t receivedCRC = packet.crc16_checksum();
    
    // Reconstruct packet with crc=0 to recalculate expected CRC
    VoicePacket verifyPacket = packet;
    verifyPacket.set_crc16_checksum(0);
    std::string verifyStr;
    if (!verifyPacket.SerializeToString(&verifyStr)) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — Verification serialization failed");
    }

    uint16_t expectedCRC = calculateCRC16(reinterpret_cast<const uint8_t*>(verifyStr.data()), verifyStr.size());
    if (static_cast<uint16_t>(receivedCRC) != expectedCRC) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — CRC16 checksum mismatch (corrupted frame rejected)");
    }

    return packet;
}

bool PacketFramer::validateFrame(const std::vector<uint8_t>& wireBytes) {
    try {
        parseAndValidateFrame(wireBytes);
        return true;
    } catch (...) {
        return false;
    }
}

} // namespace itantra::protocol
