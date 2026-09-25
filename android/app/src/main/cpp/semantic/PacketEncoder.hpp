#pragma once

// ─────────────────────────────────────────────────────────────────────────────
// PacketEncoder.hpp
//
// WHY THIS EXISTS:
//   The encoder is M3's outbound pipeline component. It accepts human-readable
//   inputs (text, language, callsign) and produces a wire-ready byte buffer
//   that can be handed to M4's transport layer.
//
// WHAT IT RECEIVES:
//   - text       : The message to transmit (UTF-8, any language)
//   - language   : BCP-47 tag ("hi", "mr", "en", …)
//   - callsign   : Operator identifier ("RESCUE_01")
//   - sequence   : Monotonically increasing packet counter
//   - priority   : 0=ROUTINE, 1=TACTICAL, 2=LIFE_SAFETY_ALERT
//
// WHAT IT PRODUCES:
//   std::vector<uint8_t> — the Protobuf-serialized packet bytes.
//
// HOW IT CONNECTS TO THE REAL ARCHITECTURE:
//   Phase 1: compressed_payload = raw UTF-8 bytes
//   Phase 2: compressed_payload = tokenized, arithmetic-coded payload
//   Phase 3: add CRC16 + AES-GCM envelope
//   The interface of encode() does NOT change across phases.
// ─────────────────────────────────────────────────────────────────────────────

#include <cstdint>
#include <string>
#include <vector>
#include "packet_schema.pb.h"
#include "SemanticCodebook.hpp"
#include "TinyMLAgent.hpp"
#include "SemanticCompressor.hpp"
#include "PacketFramer.hpp"

class PacketEncoder {
public:
    /// Legacy Phase 1 method: encodes raw text (or semantic compression) into Protobuf bytes
    std::vector<uint8_t> encode(
        const std::string& text,
        const std::string& language,
        const std::string& callsign,
        uint32_t sequence,
        uint32_t priority
    );

    /// Full semantic encode with prosody vector support
    std::vector<uint8_t> encodeSemantic(
        const itantra::semantic::SemanticResult& result,
        const std::string& callsign,
        uint32_t sequence,
        uint32_t priority,
        const std::vector<uint8_t>& prosodyVector = {}
    );
};

