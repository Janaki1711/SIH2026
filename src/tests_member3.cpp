// ─────────────────────────────────────────────────────────────────────────────
// tests_member3.cpp — Comprehensive Unit & Integration Tests for Member 3
//
// Tests:
//   Test 1: Simple emergency ("Help, there is a flood.") -> Tier 1 Macro (6-8B)
//   Test 2: Structured emergency ("Five people are trapped near Tolankere because of flooding.") -> Tier 2 (18-22B)
//   Test 3: Unknown arbitrary sentence -> Tier 3 Fallback (35-38B)
//   Test 4: Multilingual input (Hindi, Kannada, Tamil, Marathi, English)
//   Test 5: Encode/decode round trip with 16-byte prosody vector
//   Test 6: CRC16 corruption rejection (1-bit flip must fail)
//   Test 7: Payload size boundary validation (Tier 1: 6-8B, Tier 2: 18-22B, Tier 3: 35-38B)
// ─────────────────────────────────────────────────────────────────────────────

#include <iostream>
#include <iomanip>
#include <cassert>
#include <string>
#include <vector>
#include "Member3Integration.hpp"
#include "SemanticCodebook.hpp"
#include "GeoResolver.hpp"
#include "PacketFramer.hpp"
#include "SemanticCompressor.hpp"

using namespace itantra::semantic;
using namespace itantra::protocol;
using namespace itantra::integration;

void printBanner(const std::string& title) {
    std::cout << "\n==========================================================\n";
    std::cout << "  " << title << "\n";
    std::cout << "==========================================================\n";
}

bool test1_SimpleEmergency() {
    printBanner("TEST 1: Simple Emergency ('Help, there is a flood.')");
    Member3Engine engine;
    auto packet = engine.processTranscript(
        "Help, there is a flood.",
        "en", "en", {}, "RESCUE_01", 101
    );

    std::cout << "Intent          : " << actionToString(packet.semanticResult.intent) << "\n";
    std::cout << "Hazard          : " << hazardToString(packet.semanticResult.hazard) << "\n";
    std::cout << "Urgency         : " << urgencyToString(packet.semanticResult.urgency) << "\n";
    std::cout << "Payload Size    : " << packet.payloadSize << " bytes\n";
    std::cout << "Total Wire Bytes: " << packet.serializedBytes.size() << " bytes\n";
    std::cout << "Compression Tier: " << compressionTierToString(packet.compressionTier) << "\n";

    assert(packet.semanticResult.intent == ActionCode::RESCUE_REQUEST);
    assert(packet.semanticResult.hazard == HazardCode::FLOOD);
    assert(packet.semanticResult.urgency == UrgencyCode::CRITICAL_SOS);
    assert(packet.compressionTier == CompressionTier::TIER_1_MACRO);
    assert(packet.payloadSize >= 6 && packet.payloadSize <= 8);

    // Verify decode
    auto decoded = engine.decodePacket(packet.serializedBytes, "en");
    assert(decoded.crcValid);
    assert(decoded.intent == ActionCode::RESCUE_REQUEST);
    assert(decoded.hazard == HazardCode::FLOOD);
    std::cout << "Decoded Output  : " << decoded.decodedText << "\n";
    std::cout << ">>> TEST 1 PASSED <<<\n";
    return true;
}

bool test2_StructuredEmergency() {
    printBanner("TEST 2: Structured Emergency ('Five people are trapped near Tolankere...')");
    Member3Engine engine;
    auto packet = engine.processTranscript(
        "Five people are trapped near Tolankere because of flooding.",
        "en", "hi", {}, "CMD_01", 102
    );

    std::cout << "Intent          : " << actionToString(packet.semanticResult.intent) << "\n";
    std::cout << "Person Count    : " << packet.semanticResult.personCount << "\n";
    std::cout << "Hazard          : " << hazardToString(packet.semanticResult.hazard) << "\n";
    std::cout << "Location        : " << packet.semanticResult.location.canonicalName
              << " (GeoID: 0x" << std::hex << packet.semanticResult.location.geoId << std::dec << ")\n";
    std::cout << "Payload Size    : " << packet.payloadSize << " bytes\n";
    std::cout << "Compression Tier: " << compressionTierToString(packet.compressionTier) << "\n";

    assert(packet.semanticResult.intent == ActionCode::RESCUE_REQUEST);
    assert(packet.semanticResult.personCount == 5);
    assert(packet.semanticResult.hazard == HazardCode::FLOOD);
    assert(packet.semanticResult.location.geoId == GeoID::TOLANKERE);
    assert(packet.compressionTier == CompressionTier::TIER_2_STRUCTURED);
    assert(packet.payloadSize >= 18 && packet.payloadSize <= 22);

    auto decoded = engine.decodePacket(packet.serializedBytes, "hi");
    assert(decoded.crcValid);
    assert(decoded.personCount == 5);
    assert(decoded.location.geoId == GeoID::TOLANKERE);
    std::cout << "Decoded Output (HI): " << decoded.decodedText << "\n";
    std::cout << ">>> TEST 2 PASSED <<<\n";
    return true;
}

bool test3_UnknownSentenceFallback() {
    printBanner("TEST 3: Unknown Arbitrary Sentence Fallback");
    Member3Engine engine;
    std::string text = "The weather forecast indicates mild clouds over the valley tomorrow morning.";
    auto packet = engine.processTranscript(text, "en", "en", {}, "CMD_01", 103);

    std::cout << "Is Fallback     : " << (packet.semanticResult.isFallback ? "YES" : "NO") << "\n";
    std::cout << "Fallback Reason : " << packet.semanticResult.fallbackReason << "\n";
    std::cout << "Payload Size    : " << packet.payloadSize << " bytes\n";
    std::cout << "Compression Tier: " << compressionTierToString(packet.compressionTier) << "\n";

    assert(packet.semanticResult.isFallback);
    assert(packet.compressionTier == CompressionTier::TIER_3_FALLBACK);
    assert(packet.payloadSize >= 35 && packet.payloadSize <= 38);

    auto decoded = engine.decodePacket(packet.serializedBytes, "en");
    assert(decoded.crcValid);
    std::cout << "Recovered Text  : " << decoded.decodedText << "\n";
    std::cout << ">>> TEST 3 PASSED <<<\n";
    return true;
}

bool test4_Multilingual() {
    printBanner("TEST 4: Multilingual Input (Hindi, Kannada, Tamil, Marathi, English)");
    Member3Engine engine;

    struct Case {
        std::string lang;
        std::string text;
        uint16_t expectedGeoId;
        ActionCode expectedIntent;
        uint32_t expectedCount;
    };

    std::vector<Case> cases = {
        {"hi", "तोलनकेरे के पास पांच लोग फंसे हुए हैं, तुरंत नाव भेजो", GeoID::TOLANKERE, ActionCode::RESCUE_REQUEST, 5},
        {"kn", "ತೊಳನಕೆರೆ ಹತ್ತಿರ ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ, ಸಹಾಯ ಕಳುಹಿಸಿ", GeoID::TOLANKERE, ActionCode::RESCUE_REQUEST, 0},
        {"ta", "தோலன்கெரே அருகில் வெள்ளம் வந்துள்ளது, உதவி தேவை", GeoID::TOLANKERE, ActionCode::RESCUE_REQUEST, 0},
        {"mr", "तोलनकेरे जवळ पूर आला आहे, तातडीने मदत पाठवा", GeoID::TOLANKERE, ActionCode::RESCUE_REQUEST, 0},
        {"en", "Five people are trapped near Tolankere because of flooding.", GeoID::TOLANKERE, ActionCode::RESCUE_REQUEST, 5}
    };

    for (const auto& c : cases) {
        auto pkt = engine.processTranscript(c.text, c.lang, c.lang);
        std::cout << "Language: " << c.lang << " | Resolved GeoID: 0x" << std::hex << pkt.semanticResult.location.geoId << std::dec << "\n";
        assert(pkt.semanticResult.location.geoId == c.expectedGeoId);
        assert(pkt.semanticResult.intent == c.expectedIntent);
        if (c.expectedCount > 0) {
            assert(pkt.semanticResult.personCount == c.expectedCount);
        }
        assert(PacketFramer::validateFrame(pkt.serializedBytes));
    }

    std::cout << ">>> TEST 4 PASSED <<<\n";
    return true;
}

bool test5_RoundTripWithProsody() {
    printBanner("TEST 5: Encode / Decode Round Trip with 16-Byte Prosody Vector");
    Member3Engine engine;
    std::vector<uint8_t> dummyProsody = {
        0xAA, 0xBB, 0xCC, 0xDD, 0x11, 0x22, 0x33, 0x44,
        0x55, 0x66, 0x77, 0x88, 0x99, 0xEE, 0xFF, 0x00
    };

    std::string text = "Five people are trapped near Tolankere because of flooding.";
    auto packet = engine.processTranscript(text, "en", "ta", dummyProsody, "RESCUE_HQ", 205, 2);

    auto decoded = engine.decodePacket(packet.serializedBytes, "ta");
    assert(decoded.crcValid);
    assert(decoded.personCount == 5);
    assert(decoded.location.geoId == GeoID::TOLANKERE);
    assert(decoded.hazard == HazardCode::FLOOD);
    assert(decoded.priority == 2);
    assert(decoded.prosodyVector == dummyProsody);

    std::cout << "Recovered Prosody Vector: " << decoded.prosodyVector.size() << " bytes (exact match!)\n";
    std::cout << "Tamil Realization       : " << decoded.decodedText << "\n";
    std::cout << ">>> TEST 5 PASSED <<<\n";
    return true;
}

bool test6_CRC16CorruptionRejection() {
    printBanner("TEST 6: CRC16 Corruption Rejection");
    Member3Engine engine;
    auto packet = engine.processTranscript("Help, there is a flood.");
    std::vector<uint8_t> corrupted = packet.serializedBytes;

    // Flip 1 bit
    corrupted[corrupted.size() / 2] ^= 0x01;

    assert(!PacketFramer::validateFrame(corrupted));
    bool rejected = false;
    try {
        engine.decodePacket(corrupted, "en");
    } catch (const std::exception& e) {
        std::cout << "Correctly caught exception: " << e.what() << "\n";
        rejected = true;
    }
    assert(rejected);
    std::cout << ">>> TEST 6 PASSED <<<\n";
    return true;
}

bool test7_PayloadSizeBoundaries() {
    printBanner("TEST 7: Payload Size Boundary Verification");

    // Tier 1
    SemanticResult t1;
    t1.intent = ActionCode::RESCUE_REQUEST;
    t1.hazard = HazardCode::FLOOD;
    t1.urgency = UrgencyCode::CRITICAL_SOS;
    t1.compressionTier = CompressionTier::TIER_1_MACRO;
    auto b1 = SemanticCompressor::compress(t1);
    std::cout << "Tier 1 payload size: " << b1.size() << " bytes (Target: 6-8B)\n";
    assert(b1.size() >= 6 && b1.size() <= 8);

    // Tier 2
    SemanticResult t2;
    t2.intent = ActionCode::RESCUE_REQUEST;
    t2.hazard = HazardCode::FLOOD;
    t2.personCount = 5;
    t2.location.geoId = GeoID::TOLANKERE;
    t2.location.canonicalName = "Tolankere";
    t2.compressionTier = CompressionTier::TIER_2_STRUCTURED;
    auto b2 = SemanticCompressor::compress(t2);
    std::cout << "Tier 2 payload size: " << b2.size() << " bytes (Target: 18-22B)\n";
    assert(b2.size() >= 18 && b2.size() <= 22);

    // Tier 3
    SemanticResult t3;
    // >= 32 chars so the capped Tier 3 payload lands in the 35-38B band.
    // (The Python twin suite uses this same 40-char sentence; a 27-char
    // filler yields only 30B and misses the band the assertion describes.)
    t3.originalText = "Arbitrary fallback text that is unparsed";
    t3.isFallback = true;
    t3.compressionTier = CompressionTier::TIER_3_FALLBACK;
    auto b3 = SemanticCompressor::compress(t3);
    std::cout << "Tier 3 payload size: " << b3.size() << " bytes (Target: 35-38B)\n";
    assert(b3.size() >= 35 && b3.size() <= 38);

    std::cout << ">>> TEST 7 PASSED <<<\n";
    return true;
}

int main() {
    std::cout << "\n==========================================================\n";
    std::cout << "  iTantra SIH 2026 — Member 3 Native C++ Test Suite\n";
    std::cout << "==========================================================\n";

    bool p1 = test1_SimpleEmergency();
    bool p2 = test2_StructuredEmergency();
    bool p3 = test3_UnknownSentenceFallback();
    bool p4 = test4_Multilingual();
    bool p5 = test5_RoundTripWithProsody();
    bool p6 = test6_CRC16CorruptionRejection();
    bool p7 = test7_PayloadSizeBoundaries();

    std::cout << "\n==========================================================\n";
    std::cout << "  FINAL RESULT: ALL 7 MANDATORY MEMBER 3 TESTS PASSED!\n";
    std::cout << "==========================================================\n\n";

    return (p1 && p2 && p3 && p4 && p5 && p6 && p7) ? 0 : 1;
}
