#include "PacketFramer.hpp"
#include <chrono>
#include <stdexcept>
#include <algorithm>
#include <cstring>
#include <cassert>

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

uint8_t PacketFramer::languageToCode(const std::string& lang) {
    if (lang == "en") return 0;
    if (lang == "hi") return 1;
    if (lang == "ta") return 2;
    if (lang == "kn") return 3;
    if (lang == "mr") return 4;
    if (lang == "te") return 5;
    if (lang == "gu") return 6;
    if (lang == "ml") return 7;
    if (lang == "or") return 8;
    if (lang == "bn") return 9;
    return 15; // other / custom
}

std::string PacketFramer::codeToLanguage(uint8_t code) {
    switch (code) {
        case 0: return "en";
        case 1: return "hi";
        case 2: return "ta";
        case 3: return "kn";
        case 4: return "mr";
        case 5: return "te";
        case 6: return "gu";
        case 7: return "ml";
        case 8: return "or";
        case 9: return "bn";
        default: return "en";
    }
}

uint16_t PacketFramer::callsignToId(const std::string& callsign) {
    uint16_t hash = 0x5A5A;
    for (char c : callsign) {
        hash = static_cast<uint16_t>((hash * 31) + static_cast<uint8_t>(c));
    }
    return hash;
}

std::string PacketFramer::idToCallsign(uint16_t id) {
    if (id == callsignToId("RESCUE_01")) return "RESCUE_01";
    if (id == callsignToId("CMD_ALPHA")) return "CMD_ALPHA";
    if (id == callsignToId("BASE_CAMP")) return "BASE_CAMP";
    return "STATION_" + std::to_string(id);
}

std::vector<std::vector<uint8_t>> PacketFramer::framePayload(
    const std::vector<uint8_t>& payload,
    const std::string& sourceLanguage,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority,
    const std::vector<uint8_t>& prosodyVector
) {
    if (payload.empty()) {
        throw std::invalid_argument("PacketFramer::framePayload — payload cannot be empty");
    }

    bool hasProsody = !prosodyVector.empty() && std::any_of(prosodyVector.begin(), prosodyVector.end(), [](uint8_t b) { return b != 0; });
    uint8_t langCode = languageToCode(sourceLanguage);
    uint8_t prio = static_cast<uint8_t>(std::min<uint32_t>(priority, 2));
    uint16_t seq16 = static_cast<uint16_t>(sequence & 0xFFFF);
    uint16_t cid16 = callsignToId(callsign);

    size_t prosodyBytes = hasProsody ? std::min<size_t>(prosodyVector.size(), 16) : 0;
    size_t unfragmentedTotalSize = 1 + 1 + 2 + 2 + 1 + payload.size() + prosodyBytes + 2;

    // Case 1: Unfragmented single frame (<= 38 bytes)
    if (unfragmentedTotalSize <= MAX_FRAME_SIZE) {
        uint8_t flags = static_cast<uint8_t>((prio << 5) | (hasProsody ? 0x10 : 0x00) | (langCode & 0x0F));
        uint8_t payloadLen = static_cast<uint8_t>(payload.size());

        std::vector<uint8_t> frame(unfragmentedTotalSize, 0);
        frame[0] = COMPACT_MAGIC;
        frame[1] = flags;
        frame[2] = static_cast<uint8_t>((seq16 >> 8) & 0xFF);
        frame[3] = static_cast<uint8_t>(seq16 & 0xFF);
        frame[4] = static_cast<uint8_t>((cid16 >> 8) & 0xFF);
        frame[5] = static_cast<uint8_t>(cid16 & 0xFF);
        frame[6] = payloadLen;

        std::memcpy(&frame[7], payload.data(), payloadLen);
        size_t offset = 7 + payloadLen;

        if (hasProsody && prosodyBytes > 0) {
            std::memcpy(&frame[offset], prosodyVector.data(), prosodyBytes);
            offset += prosodyBytes;
        }

        uint16_t crc = calculateCRC16(frame.data(), offset);
        frame[offset]     = static_cast<uint8_t>((crc >> 8) & 0xFF);
        frame[offset + 1] = static_cast<uint8_t>(crc & 0xFF);

        assert(frame.size() <= MAX_FRAME_SIZE);
        return { frame };
    }

    // Case 2: Fragmented into multiple <=38B frames (Each chunk <= 27 bytes)
    size_t totalBytes = payload.size();
    size_t numFragments = (totalBytes + MAX_FRAGMENT_PAYLOAD - 1) / MAX_FRAGMENT_PAYLOAD;
    if (numFragments > 255) {
        throw std::runtime_error("PacketFramer::framePayload — payload exceeds maximum fragment limit (255)");
    }

    std::vector<std::vector<uint8_t>> frames;
    frames.reserve(numFragments);

    uint8_t flags = static_cast<uint8_t>(FLAG_FRAGMENTED | (prio << 5) | (langCode & 0x0F));

    for (size_t i = 0; i < numFragments; ++i) {
        size_t startOffset = i * MAX_FRAGMENT_PAYLOAD;
        size_t chunkLen = std::min<size_t>(MAX_FRAGMENT_PAYLOAD, totalBytes - startOffset);
        size_t frameSize = FRAGMENTED_HEADER_SIZE + chunkLen + CRC_SIZE; // 9 + chunkLen + 2 = 11 + chunkLen <= 38

        std::vector<uint8_t> frame(frameSize, 0);
        frame[0] = COMPACT_MAGIC;
        frame[1] = flags;
        frame[2] = static_cast<uint8_t>((seq16 >> 8) & 0xFF);
        frame[3] = static_cast<uint8_t>(seq16 & 0xFF);
        frame[4] = static_cast<uint8_t>((cid16 >> 8) & 0xFF);
        frame[5] = static_cast<uint8_t>(cid16 & 0xFF);
        frame[6] = static_cast<uint8_t>(i);
        frame[7] = static_cast<uint8_t>(numFragments);
        frame[8] = static_cast<uint8_t>(chunkLen);

        std::memcpy(&frame[9], &payload[startOffset], chunkLen);

        uint16_t crc = calculateCRC16(frame.data(), 9 + chunkLen);
        frame[9 + chunkLen]     = static_cast<uint8_t>((crc >> 8) & 0xFF);
        frame[9 + chunkLen + 1] = static_cast<uint8_t>(crc & 0xFF);

        assert(frame.size() <= MAX_FRAME_SIZE);
        frames.push_back(frame);
    }

    return frames;
}

std::vector<uint8_t> PacketFramer::framePacket(
    const std::vector<uint8_t>& compressedPayload,
    const std::string& sourceLanguage,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority,
    const std::vector<uint8_t>& prosodyVector
) {
    auto frames = framePayload(compressedPayload, sourceLanguage, callsign, sequence, priority, prosodyVector);
    return frames.empty() ? std::vector<uint8_t>() : frames[0];
}

VoicePacket PacketFramer::parseAndValidateFrame(const std::vector<uint8_t>& wireBytes) {
    if (wireBytes.empty()) {
        throw std::invalid_argument("PacketFramer::parseAndValidateFrame — received empty byte buffer");
    }

    // Mode 1: Ultra-Compact Binary Frame (Magic 0x53)
    if (wireBytes[0] == COMPACT_MAGIC && wireBytes.size() >= 9) {
        size_t n = wireBytes.size();
        uint16_t receivedCRC = (static_cast<uint16_t>(wireBytes[n - 2]) << 8) | static_cast<uint16_t>(wireBytes[n - 1]);
        uint16_t expectedCRC = calculateCRC16(wireBytes.data(), n - 2);

        if (receivedCRC != expectedCRC) {
            throw std::runtime_error("PacketFramer::parseAndValidateFrame — CRC16 checksum mismatch (corrupted frame rejected)");
        }

        uint8_t flags = wireBytes[1];
        bool isFragmented = (flags & FLAG_FRAGMENTED) != 0;
        uint8_t prio = (flags >> 5) & 0x03;
        bool hasProsody = !isFragmented && ((flags & 0x10) != 0);
        uint8_t langCode = flags & 0x0F;

        uint16_t seq = (static_cast<uint16_t>(wireBytes[2]) << 8) | static_cast<uint16_t>(wireBytes[3]);
        uint16_t cid = (static_cast<uint16_t>(wireBytes[4]) << 8) | static_cast<uint16_t>(wireBytes[5]);

        VoicePacket packet;
        packet.set_magic_header(MAGIC_HEADER);
        packet.set_sequence_number(seq);
        packet.set_priority(static_cast<PriorityLevel>(prio));
        packet.set_source_language(codeToLanguage(langCode));
        packet.set_source_callsign(idToCallsign(cid));
        packet.set_crc16_checksum(receivedCRC);

        if (isFragmented) {
            if (wireBytes.size() < 11) {
                throw std::runtime_error("PacketFramer::parseAndValidateFrame — Fragmented frame too short");
            }
            uint8_t fragIdx = wireBytes[6];
            uint8_t totalFrags = wireBytes[7];
            uint8_t payloadLen = wireBytes[8];
            if (9 + payloadLen > n - 2) {
                throw std::runtime_error("PacketFramer::parseAndValidateFrame — Invalid fragment payload length");
            }
            std::string payloadStr(reinterpret_cast<const char*>(&wireBytes[9]), payloadLen);
            packet.set_compressed_payload(payloadStr);
        } else {
            uint8_t payloadLen = wireBytes[6];
            if (7 + payloadLen > n - 2) {
                throw std::runtime_error("PacketFramer::parseAndValidateFrame — Invalid payload length");
            }
            std::string payloadStr(reinterpret_cast<const char*>(&wireBytes[7]), payloadLen);
            packet.set_compressed_payload(payloadStr);

            size_t prosodyOffset = 7 + payloadLen;
            size_t prosodyLen = (n - 2 > prosodyOffset) ? (n - 2 - prosodyOffset) : 0;
            if (hasProsody && prosodyLen > 0) {
                std::string pVec(reinterpret_cast<const char*>(&wireBytes[prosodyOffset]), prosodyLen);
                if (pVec.size() < 16) pVec.resize(16, 0);
                packet.set_prosody_vector(pVec);
            }
        }

        return packet;
    }

    // Mode 2: Legacy Protobuf Frame Fallback
    VoicePacket packet;
    std::string rawStr(reinterpret_cast<const char*>(wireBytes.data()), wireBytes.size());
    if (!packet.ParseFromString(rawStr)) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — Deserialization failed (unrecognized format)");
    }

    if (packet.magic_header() != MAGIC_HEADER) {
        throw std::runtime_error("PacketFramer::parseAndValidateFrame — Invalid magic header (sync word mismatch)");
    }

    uint32_t receivedCRC = packet.crc16_checksum();
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

ReassemblyResult MessageReassembler::processFrame(const std::vector<uint8_t>& frameBytes) {
    ReassemblyResult res;
    if (frameBytes.empty()) return res;

    // Validate and parse basic frame
    VoicePacket pkt;
    try {
        pkt = PacketFramer::parseAndValidateFrame(frameBytes);
    } catch (...) {
        return res; // Invalid or corrupted CRC
    }

    // Check if frame is compact binary with fragmentation
    if (frameBytes[0] == PacketFramer::COMPACT_MAGIC && (frameBytes[1] & PacketFramer::FLAG_FRAGMENTED) != 0) {
        if (frameBytes.size() < 11) return res;

        uint16_t seq = (static_cast<uint16_t>(frameBytes[2]) << 8) | static_cast<uint16_t>(frameBytes[3]);
        uint16_t cid = (static_cast<uint16_t>(frameBytes[4]) << 8) | static_cast<uint16_t>(frameBytes[5]);
        uint8_t fragIdx = frameBytes[6];
        uint8_t totalFrags = frameBytes[7];
        uint8_t payloadLen = frameBytes[8];

        std::string sessionKey = std::to_string(seq) + "-" + std::to_string(cid);
        auto& session = sessions_[sessionKey];
        session.sequence = seq;
        session.callsignId = cid;
        session.flags = frameBytes[1];
        session.totalFragments = totalFrags;
        session.lastUpdate = std::chrono::steady_clock::now();

        std::vector<uint8_t> chunk(frameBytes.begin() + 9, frameBytes.begin() + 9 + payloadLen);
        session.fragments[fragIdx] = chunk;

        res.receivedFragments = static_cast<uint32_t>(session.fragments.size());
        res.totalFragments = totalFrags;

        // Check if all fragments arrived (0..totalFrags-1)
        if (session.fragments.size() == totalFrags) {
            std::vector<uint8_t> fullPayload;
            for (uint8_t i = 0; i < totalFrags; ++i) {
                if (session.fragments.find(i) == session.fragments.end()) {
                    return res; // Gap in fragments
                }
                const auto& c = session.fragments[i];
                fullPayload.insert(fullPayload.end(), c.begin(), c.end());
            }

            res.isComplete = true;
            res.packet = pkt;
            std::string fullPayloadStr(fullPayload.begin(), fullPayload.end());
            res.packet.set_compressed_payload(fullPayloadStr);

            sessions_.erase(sessionKey);
            return res;
        }

        return res; // Still waiting for more fragments
    }

    // Unfragmented frame -> Immediately complete
    res.isComplete = true;
    res.packet = pkt;
    res.receivedFragments = 1;
    res.totalFragments = 1;
    return res;
}

void MessageReassembler::cleanupOldSessions(uint64_t maxAgeSeconds) {
    auto now = std::chrono::steady_clock::now();
    for (auto it = sessions_.begin(); it != sessions_.end(); ) {
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - it->second.lastUpdate).count();
        if (static_cast<uint64_t>(elapsed) > maxAgeSeconds) {
            it = sessions_.erase(it);
        } else {
            ++it;
        }
    }
}

} // namespace itantra::protocol
