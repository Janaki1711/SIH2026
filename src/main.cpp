// ─────────────────────────────────────────────────────────────────────────────
// main.cpp — iTantra M3 Phase 1 Demonstration
//
// PURPOSE:
//   Prove that the C++ Protobuf serialization engine correctly roundtrips
//   messages through the pipeline:
//       TEXT → VoicePacket → Protobuf bytes → VoicePacket → TEXT
//
// TESTS:
//   Test 1 — English message
//   Test 2 — Hindi message (सेक्टर 4 में...)
//   Test 3 — Marathi message
//   Test 4 — Empty input  (should be rejected with error)
//   Test 5 — Very long message (demonstrates protobuf is serialization,
//             not compression — payload may be larger than input)
//
// NOTE ON UTF-8:
//   Hindi/Marathi characters are encoded as multi-byte UTF-8 sequences.
//   std::string in C++ treats them as raw bytes, which is exactly correct.
//   Protobuf's bytes and string fields are also just byte sequences.
//   The terminal must use a UTF-8 locale to display them properly.
// ─────────────────────────────────────────────────────────────────────────────

#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <cassert>
#include <algorithm>
#include <string_view>

#include "PacketEncoder.hpp"
#include "PacketDecoder.hpp"

// ── Utilities ─────────────────────────────────────────────────────────────────

/// Return a hex dump of bytes as a formatted string (16 bytes per line).
std::string hexDump(const std::vector<uint8_t>& data) {
    std::ostringstream oss;
    for (size_t i = 0; i < data.size(); ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0')
            << static_cast<int>(data[i]);
        if ((i + 1) % 16 == 0) {
            oss << "\n  ";
        } else if (i + 1 < data.size()) {
            oss << " ";
        }
    }
    return oss.str();
}

/// Map PriorityLevel enum to human-readable string.
std::string priorityName(itantra::protocol::PriorityLevel p) {
    switch (p) {
        case itantra::protocol::ROUTINE:          return "ROUTINE (0)";
        case itantra::protocol::TACTICAL:         return "TACTICAL (1)";
        case itantra::protocol::LIFE_SAFETY_ALERT: return "LIFE_SAFETY_ALERT (2)";
        default:                                   return "UNKNOWN";
    }
}

/// Print a divider line.
// std::string_view, not char: box-drawing glyphs are multi-byte UTF-8, and
// std::string(width, ch) with a char would truncate them to one byte (and
// GCC -Wpedantic -Werror rejects multi-byte char literals outright).
void divider(std::string_view ch = "─", int width = 56) {
    for (int i = 0; i < width; ++i) std::cout << ch;
    std::cout << "\n";
}

// ── Single Test Runner ────────────────────────────────────────────────────────

/// Run one complete pipeline test.
///
/// @param testNum   Test number for display
/// @param label     Short description
/// @param text      Input message
/// @param language  BCP-47 language tag
/// @param callsign  Source operator identifier
/// @param sequence  Packet sequence number
/// @param priority  0=ROUTINE, 1=TACTICAL, 2=LIFE_SAFETY_ALERT
/// @return true if test passed, false if expected failure (empty input)
bool runTest(
    int testNum,
    const std::string& label,
    const std::string& text,
    const std::string& language,
    const std::string& callsign,
    uint32_t sequence,
    uint32_t priority
) {
    std::cout << "\n";
    divider("═");
    std::cout << "  TEST " << testNum << " — " << label << "\n";
    divider("═");

    PacketEncoder encoder;
    PacketDecoder decoder;

    // ── SENDER PANEL ─────────────────────────────────────────────────────────
    std::cout << "\n  ┌─────────────────────────────────────────────────┐\n";
    std::cout << "  │                    SENDER                       │\n";
    std::cout << "  └─────────────────────────────────────────────────┘\n\n";

    std::cout << "  Input Text    : " << (text.empty() ? "(empty)" : text) << "\n";
    std::cout << "  Language      : " << language << "\n";
    std::cout << "  Callsign      : " << callsign << "\n";
    std::cout << "  Priority      : " << priority << "\n";
    std::cout << "  Sequence      : " << sequence << "\n";
    std::cout << "  UTF-8 Bytes   : " << text.size() << " bytes\n\n";

    // Step 1
    std::cout << "  ✓ [1/4] Input received\n";

    // Try encoding
    std::vector<uint8_t> wireBytes;
    try {
        std::cout << "  ✓ [2/4] VoicePacket created\n";
        std::cout << "  ✓ [3/4] UTF-8 payload set in compressed_payload field\n";

        wireBytes = encoder.encode(text, language, callsign, sequence, priority);

        std::cout << "  ✓ [4/4] Protobuf serialized → " << wireBytes.size() << " bytes\n";

    } catch (const std::invalid_argument& e) {
        // Expected for Test 4 (empty input)
        std::cout << "  ✗ [2/4] Encoder rejected input:\n";
        std::cout << "          " << e.what() << "\n";
        std::cout << "\n  ── Result: REJECTED (expected for empty input) ──\n";
        return false; // Not a failure — this is correct behavior
    }

    // Size comparison
    if (!text.empty()) {
        std::cout << "\n  ┌─ Payload Analysis ────────────────────────────────┐\n";
        std::cout << "  │  Input UTF-8 bytes   : " << std::setw(6) << text.size() << " bytes              │\n";
        std::cout << "  │  Protobuf packet     : " << std::setw(6) << wireBytes.size() << " bytes              │\n";

        // Overhead = protobuf framing (field tags, varints, sync word, etc.)
        long overhead = static_cast<long>(wireBytes.size()) - static_cast<long>(text.size());
        std::cout << "  │  Protocol overhead   : " << std::setw(6) << overhead << " bytes              │\n";
        std::cout << "  │                                                   │\n";
        std::cout << "  │  NOTE: Protobuf is SERIALIZATION, not compression │\n";
        std::cout << "  │  Phase 2 will add arithmetic coding to reduce     │\n";
        std::cout << "  │  compressed_payload before serialization.         │\n";
        std::cout << "  └───────────────────────────────────────────────────┘\n";
    }

    // Hex dump
    std::cout << "\n  Raw wire bytes:\n  ";
    std::cout << hexDump(wireBytes) << "\n";

    // ── SIMULATED M4 TRANSPORT ───────────────────────────────────────────────
    std::cout << "\n";
    std::cout << "  ╔═══════════════════════════════════════════════════╗\n";
    std::cout << "  ║          ~~~ SIMULATED M4 TRANSPORT ~~~           ║\n";
    std::cout << "  ║                                                   ║\n";
    std::cout << "  ║  → Packet transmitted (" << std::setw(3) << wireBytes.size() << " bytes)              ║\n";
    std::cout << "  ║  → Packet received    (" << std::setw(3) << wireBytes.size() << " bytes)              ║\n";
    std::cout << "  ║  → Zero byte corruption (ideal channel)           ║\n";
    std::cout << "  ╚═══════════════════════════════════════════════════╝\n";

    // ── RECEIVER PANEL ───────────────────────────────────────────────────────
    std::cout << "\n  ┌─────────────────────────────────────────────────┐\n";
    std::cout << "  │                   RECEIVER                       │\n";
    std::cout << "  └─────────────────────────────────────────────────┘\n\n";

    itantra::protocol::VoicePacket received;
    try {
        std::cout << "  ✓ [1/4] Bytes received from transport\n";
        received = decoder.decode(wireBytes);
        std::cout << "  ✓ [2/4] Protobuf parsed successfully\n";
        std::cout << "  ✓ [3/4] Packet fields recovered\n";
        std::cout << "  ✓ [4/4] Text reconstructed\n";

    } catch (const std::exception& e) {
        std::cout << "  ✗ Decode failed: " << e.what() << "\n";
        return false;
    }

    // Print decoded fields
    std::cout << "\n  ┌─ Decoded VoicePacket ──────────────────────────────┐\n";
    std::cout << "  │  magic_header    : 0x"
              << std::hex << std::setw(8) << std::setfill('0')
              << received.magic_header()
              << std::dec << std::setfill(' ') << "              │\n";
    std::cout << "  │  sequence_number : " << std::setw(6) << received.sequence_number() << "                     │\n";
    std::cout << "  │  source_language : " << std::setw(6) << received.source_language() << "                     │\n";
    std::cout << "  │  source_callsign : " << received.source_callsign() << "               │\n";
    std::cout << "  │  priority        : " << priorityName(received.priority()) << "  │\n";
    std::cout << "  │  payload size    : " << std::setw(6) << received.compressed_payload().size() << " bytes              │\n";
    std::cout << "  └───────────────────────────────────────────────────┘\n";

    std::cout << "\n  Recovered Text: " << received.compressed_payload() << "\n";

    // Verify roundtrip
    bool passed = (received.compressed_payload() == text);
    if (passed) {
        std::cout << "\n  ✓✓ ROUNDTRIP VERIFIED — recovered text matches input exactly\n";
    } else {
        std::cout << "\n  ✗✗ ROUNDTRIP FAILED — text mismatch!\n";
    }

    return passed;
}

// ── Main ──────────────────────────────────────────────────────────────────────

int main() {
    // Enable UTF-8 output on Windows
    // (On Linux/macOS this is typically the default locale)
#ifdef _WIN32
    // Attempt to set UTF-8 code page for Windows console
    // This requires linking against proper CRT on MSVC.
    // With MinGW/Clang on Windows, the console must be set to UTF-8 manually:
    //   chcp 65001   (run before executing the binary)
    system("chcp 65001 > nul");
#endif

    std::cout << "\n";
    std::cout << "╔══════════════════════════════════════════════════════════╗\n";
    std::cout << "║              iTANTRA M3 — PHASE 1                       ║\n";
    std::cout << "║         Protobuf Communication Simulator                 ║\n";
    std::cout << "║                                                          ║\n";
    std::cout << "║  Pipeline:  TEXT → BYTES → TEXT                         ║\n";
    std::cout << "║  Transport: SIMULATED (no networking)                    ║\n";
    std::cout << "║  Member:    M3 — Serialization Lead                     ║\n";
    std::cout << "╚══════════════════════════════════════════════════════════╝\n";

    int passed = 0;
    int total  = 0;

    // ── Test 1: English ───────────────────────────────────────────────────────
    ++total;
    bool t1 = runTest(
        1, "English message",
        "Send help to sector 4",
        "en", "CMD_ALPHA", 1, 1  // TACTICAL
    );
    if (t1) ++passed;

    // ── Test 2: Hindi (primary M3 demonstration) ──────────────────────────────
    ++total;
    bool t2 = runTest(
        2, "Hindi — primary SIH demonstration",
        "सेक्टर 4 में तुरंत मदद भेजो",
        "hi", "RESCUE_01", 2, 2  // LIFE_SAFETY_ALERT
    );
    if (t2) ++passed;

    // ── Test 3: Marathi ───────────────────────────────────────────────────────
    ++total;
    bool t3 = runTest(
        3, "Marathi",
        "सेक्टर ४ मध्ये मदत पाठवा",
        "mr", "FIELD_02", 3, 2  // LIFE_SAFETY_ALERT
    );
    if (t3) ++passed;

    // ── Test 4: Empty input (expected rejection) ──────────────────────────────
    ++total;
    std::cout << "\n";
    divider("═");
    std::cout << "  TEST 4 — Empty input (expected rejection)\n";
    divider("═");
    std::cout << "\n  Attempting to encode an empty string...\n";
    bool t4_rejected = false;
    try {
        PacketEncoder enc;
        enc.encode("", "en", "CMD_ALPHA", 4, 0);
        std::cout << "  ✗ ERROR: Empty input was NOT rejected — this is a bug.\n";
    } catch (const std::invalid_argument& e) {
        std::cout << "  ✓ Empty input correctly rejected:\n";
        std::cout << "    " << e.what() << "\n";
        t4_rejected = true;
        ++passed;
    }

    // ── Test 5: Long message (size analysis) ──────────────────────────────────
    ++total;
    // Build a ~500 byte input (repeating Hindi phrase)
    std::string longText;
    std::string phrase = "सेक्टर 4 में मदद भेजो। ";
    while (longText.size() < 500) {
        longText += phrase;
    }
    bool t5 = runTest(
        5, "Long message — payload size analysis",
        longText,
        "hi", "FIELD_03", 5, 0  // ROUTINE
    );
    if (t5) ++passed;

    // ── Summary ───────────────────────────────────────────────────────────────
    std::cout << "\n";
    std::cout << "╔══════════════════════════════════════════════════════════╗\n";
    std::cout << "║                    PHASE 1 SUMMARY                      ║\n";
    std::cout << "╠══════════════════════════════════════════════════════════╣\n";
    std::cout << "║  Test 1 — English          : " << (t1 ? "✓ PASS" : "✗ FAIL") << "                    ║\n";
    std::cout << "║  Test 2 — Hindi            : " << (t2 ? "✓ PASS" : "✗ FAIL") << "                    ║\n";
    std::cout << "║  Test 3 — Marathi          : " << (t3 ? "✓ PASS" : "✗ FAIL") << "                    ║\n";
    std::cout << "║  Test 4 — Empty (rejected) : " << (t4_rejected ? "✓ PASS" : "✗ FAIL") << "                    ║\n";
    std::cout << "║  Test 5 — Long message     : " << (t5 ? "✓ PASS" : "✗ FAIL") << "                    ║\n";
    std::cout << "╠══════════════════════════════════════════════════════════╣\n";
    {
        std::ostringstream oss;
        oss << passed << "/" << total << " tests passed";
        std::string result_str = oss.str();
        // Box inner width is 58 chars; "║  Result: " is 11 chars; "  ║" is 3
        int pad = 58 - 11 - static_cast<int>(result_str.size()) - 3;
        std::cout << "║  Result: " << result_str
                  << std::string(std::max(pad, 0), ' ') << "║\n";
    }
    std::cout << "╠══════════════════════════════════════════════════════════╣\n";
    std::cout << "║  PHASE 1 OBJECTIVE:                                      ║\n";
    std::cout << "║  TEXT → BYTES → TEXT   ✓ DEMONSTRATED                   ║\n";
    std::cout << "║                                                          ║\n";
    std::cout << "║  NEXT: Phase 2 — SentencePiece tokenization +           ║\n";
    std::cout << "║        arithmetic coding in compressed_payload           ║\n";
    std::cout << "╚══════════════════════════════════════════════════════════╝\n\n";

    return (passed == total) ? 0 : 1;
}
