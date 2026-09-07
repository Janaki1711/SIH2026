// ─────────────────────────────────────────────────────────────────────────────
// PacketEncoder.cpp
//
// WHAT THIS FILE DOES:
//   Implements the Sender half of the iTantra M3 Phase 1 pipeline:
//
//     Input text (UTF-8)
//         │
//         ▼
//     VoicePacket (Protobuf message)
//         │   ← set_magic_header   (sync word: 0x41475931)
//         │   ← set_sequence_number
//         │   ← set_timestamp_ms   (system clock, milliseconds)
//         │   ← set_priority
//         │   ← set_source_callsign
//         │   ← set_source_language
//         │   ← set_compressed_payload  (Phase 1: raw UTF-8 bytes)
//         │
//         ▼
//     packet.SerializeToString(&serialized)
//         │
//         ▼
//     std::vector<uint8_t>   ← wire-ready byte buffer
//
// WHY PROTOBUF SerializeToString():
//   Protobuf uses field tags + varint encoding, not a fixed-layout struct.
//   This means the output is compact but self-describing — each field carries
//   its field number so the receiver can reconstruct the message even if field
//   order changes in a future schema revision.
//
// WHY compressed_payload = raw text in Phase 1:
//   The interface is intentionally stable. In Phase 2, this line becomes:
//       packet.set_compressed_payload(arithmetic_encode(tokenize(text)));
//   The rest of the encoder doesn't change.
// ─────────────────────────────────────────────────────────────────────────────

#include "PacketEncoder.hpp"

#include <chrono>
#include <stdexcept>

#include "PacketEncoder.hpp"
#include <chrono>
#include <stdexcept>

std::vector<uint8_t> PacketEncoder::encode(
    const std::string& text,
    const std::string& language,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority
) {
    if (text.empty()) {
        throw std::invalid_argument(
            "PacketEncoder::encode — text payload must not be empty"
        );
    }

    // Wrap raw UTF-8 as compressed payload
    std::vector<uint8_t> payload(text.begin(), text.end());
    return itantra::protocol::PacketFramer::framePacket(
        payload,
        language,
        callsign,
        sequence,
        priority
    );
}

std::vector<uint8_t> PacketEncoder::encodeSemantic(
    const itantra::semantic::SemanticResult& result,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority,
    const std::vector<uint8_t>& prosodyVector
) {
    std::vector<uint8_t> compressedPayload = itantra::semantic::SemanticCompressor::compress(result);
    return itantra::protocol::PacketFramer::framePacket(
        compressedPayload,
        result.detectedLanguage,
        callsign,
        sequence,
        priority,
        prosodyVector.empty() ? result.prosodyVector : prosodyVector
    );
}

