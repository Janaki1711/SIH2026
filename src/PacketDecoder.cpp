// ─────────────────────────────────────────────────────────────────────────────
// PacketDecoder.cpp
//
// WHAT THIS FILE DOES:
//   Implements the Receiver half of the iTantra M3 Phase 1 pipeline:
//
//     std::vector<uint8_t>   ← raw bytes from M4 transport
//         │
//         ▼
//     std::string (reinterpreted — no copy of data, just a view)
//         │
//         ▼
//     packet.ParseFromString(serialized)
//         │
//         ▼
//     itantra::protocol::VoicePacket  ← fully populated
//         │
//         ├── sequence_number()
//         ├── source_language()
//         ├── source_callsign()
//         ├── priority()
//         └── compressed_payload()   ← Phase 1: recovered UTF-8 text
//
// WHY ParseFromString() and NOT ParseFromArray():
//   Both work. ParseFromString() is slightly simpler and produces identical
//   results for our use case. ParseFromArray() is preferred on embedded targets
//   where the byte array is not already in a string-compatible form.
//
// IMPORTANT — what Protobuf does NOT do for you:
//   Protobuf does not validate that magic_header == 0x41475931.
//   It does not check sequence continuity.
//   It does not verify data integrity (no checksum in Phase 1).
//   Phase 3 will add CRC16 validation before ParseFromString() is called.
// ─────────────────────────────────────────────────────────────────────────────

#include "PacketDecoder.hpp"

#include <stdexcept>

itantra::protocol::VoicePacket PacketDecoder::decode(
    const std::vector<uint8_t>& data
) {
    if (data.empty()) {
        throw std::invalid_argument(
            "PacketDecoder::decode — received empty byte buffer"
        );
    }

    itantra::protocol::VoicePacket packet;

    // Reinterpret the byte vector as a string.
    // Protobuf's ParseFromString() accepts std::string containing binary data.
    // This is a single allocation; the bytes are owned by `data`.
    std::string serialized(
        reinterpret_cast<const char*>(data.data()),
        data.size()
    );

    if (!packet.ParseFromString(serialized)) {
        throw std::runtime_error(
            "PacketDecoder::decode — Protobuf deserialization failed. "
            "Possible causes: corrupted bytes, wrong schema version, "
            "or non-iTantra packet."
        );
    }

    // Phase 1: We trust the magic_header is present but do not hard-fail on it.
    // This is a conscious Phase 1 decision — we are testing the serialization
    // path, not the full protocol validation path.
    //
    // Phase 3 addition (do NOT implement now):
    //   if (packet.magic_header() != 0x41475931) {
    //       throw std::runtime_error("Invalid magic header — not an iTantra packet");
    //   }

    return packet;
}
