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

std::vector<uint8_t> PacketEncoder::encode(
    const std::string& text,
    const std::string& language,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority
) {
    // ── Validation ────────────────────────────────────────────────────────────
    // Empty payloads are rejected here. A zero-length compressed_payload is a
    // protocol error in any phase, so we enforce it at the encoder level.
    if (text.empty()) {
        throw std::invalid_argument(
            "PacketEncoder::encode — text payload must not be empty"
        );
    }

    // ── Build VoicePacket ─────────────────────────────────────────────────────
    itantra::protocol::VoicePacket packet;

    // Sync word: 0x41475931 = "AGY1" in ASCII.
    // M4's receiver will look for this value to identify iTantra packets
    // among other traffic on the shared RF channel.
    packet.set_magic_header(0x41475931);

    // Packet counter. Receiver uses this to detect dropped packets.
    packet.set_sequence_number(sequence);

    // Capture current time as milliseconds since UNIX epoch.
    // Used for latency measurement and replay-attack detection (Phase 3).
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
    packet.set_timestamp_ms(static_cast<uint64_t>(now_ms));

    // Priority level. Validates the cast is within enum range.
    if (priority > 2) {
        throw std::invalid_argument(
            "PacketEncoder::encode — priority must be 0 (ROUTINE), "
            "1 (TACTICAL), or 2 (LIFE_SAFETY_ALERT)"
        );
    }
    packet.set_priority(
        static_cast<itantra::protocol::PriorityLevel>(priority)
    );

    packet.set_source_callsign(callsign);
    packet.set_source_language(language);

    // ── PHASE 1: compressed_payload = raw UTF-8 bytes ─────────────────────────
    // We store the text string directly. Protobuf's bytes field accepts
    // std::string, and UTF-8 is a valid byte sequence.
    //
    // Phase 2 replacement:
    //     auto tokens   = sentencepiece_encode(text);
    //     auto payload  = arithmetic_encode(tokens);
    //     packet.set_compressed_payload(payload);
    packet.set_compressed_payload(text);

    // prosody_vector is left empty in Phase 1.
    // Phase 4 will populate it from the TTS prosody predictor.

    // ── Serialize ─────────────────────────────────────────────────────────────
    std::string serialized;
    if (!packet.SerializeToString(&serialized)) {
        throw std::runtime_error(
            "PacketEncoder::encode — Protobuf serialization failed"
        );
    }

    // Return as an owned byte vector.
    // This is the exact buffer that would be handed to M4's transport layer.
    return std::vector<uint8_t>(serialized.begin(), serialized.end());
}
