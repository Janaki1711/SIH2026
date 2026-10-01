#include "SemanticCompressor.hpp"
#include <stdexcept>
#include <cstring>
#include <algorithm>

namespace itantra::semantic {

std::vector<uint8_t> SemanticCompressor::encodeTier1(const SemanticResult& res) {
    // Tier 1 Layout: 6 bytes
    // Byte 0: Tier Header (0x01, or 0x81 if isNegated)
    // Byte 1: (Intent & 0x0F) << 4 | (Urgency & 0x0F)
    // Byte 2: (Action & 0x0F) << 4 | (Hazard & 0x0F)
    // Byte 3: Person Count (0..255)
    // Bytes 4-5: GeoID (uint16_t big-endian)
    std::vector<uint8_t> buf(6);
    buf[0] = static_cast<uint8_t>(res.isNegated ? 0x81 : 0x01);
    buf[1] = ((static_cast<uint8_t>(res.intent) & 0x0F) << 4) | (static_cast<uint8_t>(res.urgency) & 0x0F);
    buf[2] = ((static_cast<uint8_t>(res.action) & 0x0F) << 4) | (static_cast<uint8_t>(res.hazard) & 0x0F);
    buf[3] = static_cast<uint8_t>(std::min<uint32_t>(res.personCount, 255));
    
    uint16_t gid = res.location.geoId;
    buf[4] = static_cast<uint8_t>((gid >> 8) & 0xFF);
    buf[5] = static_cast<uint8_t>(gid & 0xFF);
    return buf;
}

SemanticResult SemanticCompressor::decodeTier1(const std::vector<uint8_t>& data) {
    if (data.size() < 6) {
        throw std::runtime_error("Tier 1 payload too short (minimum 6 bytes required)");
    }
    SemanticResult res;
    res.compressionTier = CompressionTier::TIER_1_MACRO;
    res.isFallback = false;
    res.isNegated = (data[0] & 0x80) != 0;
    res.confidence = 0.95f;

    res.intent  = static_cast<ActionCode>((data[1] >> 4) & 0x0F);
    res.urgency = static_cast<UrgencyCode>(data[1] & 0x0F);
    res.action  = static_cast<ActionCode>((data[2] >> 4) & 0x0F);
    res.hazard  = static_cast<HazardCode>(data[2] & 0x0F);
    res.personCount = data[3];

    uint16_t gid = (static_cast<uint16_t>(data[4]) << 8) | static_cast<uint16_t>(data[5]);
    res.location.geoId = gid;
    res.location.canonicalName = geoIdToString(gid);
    res.location.confidence = 0.95f;

    return res;
}

std::vector<uint8_t> SemanticCompressor::encodeTier2(const SemanticResult& res) {
    // Tier 2 Layout: 18 bytes
    // Byte 0: Tier Header (0x02, or 0x82 if isNegated)
    // Byte 1: Intent (uint8_t)
    // Byte 2: Action (uint8_t)
    // Byte 3: Hazard (uint8_t)
    // Byte 4: Urgency (uint8_t)
    // Bytes 5-6: Person Count (uint16_t big-endian)
    // Bytes 7-8: GeoID (uint16_t big-endian)
    // Byte 9: Confidence (0..100)
    // Bytes 10-11: Language tag (2 bytes, e.g. "hi", "en", "kn")
    // Bytes 12-13: Sub-entity/status flags (Byte 12 Bit 0: isNegated)
    // Bytes 14-17: Context flags / Timestamp delta (uint32_t big-endian)
    std::vector<uint8_t> buf(18, 0);
    buf[0] = static_cast<uint8_t>(res.isNegated ? 0x82 : 0x02);
    buf[1] = static_cast<uint8_t>(res.intent);
    buf[2] = static_cast<uint8_t>(res.action);
    buf[3] = static_cast<uint8_t>(res.hazard);
    buf[4] = static_cast<uint8_t>(res.urgency);

    uint16_t count16 = static_cast<uint16_t>(std::min<uint32_t>(res.personCount, 65535));
    buf[5] = static_cast<uint8_t>((count16 >> 8) & 0xFF);
    buf[6] = static_cast<uint8_t>(count16 & 0xFF);

    uint16_t gid = res.location.geoId;
    buf[7] = static_cast<uint8_t>((gid >> 8) & 0xFF);
    buf[8] = static_cast<uint8_t>(gid & 0xFF);

    buf[9] = static_cast<uint8_t>(std::clamp<int>(static_cast<int>(res.confidence * 100.0f), 0, 100));

    std::string lang = res.detectedLanguage.empty() ? "en" : res.detectedLanguage;
    buf[10] = static_cast<uint8_t>(lang.size() > 0 ? lang[0] : 'e');
    buf[11] = static_cast<uint8_t>(lang.size() > 1 ? lang[1] : 'n');

    // Sub-entity/status flags (bytes 12-13)
    buf[12] = res.isNegated ? 0x01 : 0x00;
    buf[13] = static_cast<uint8_t>(res.extractedEntities.size() & 0xFF);

    // Context flags (bytes 14-17)
    buf[14] = 0x00;
    buf[15] = 0x00;
    buf[16] = 0x00;
    buf[17] = 0x00;

    return buf;
}

SemanticResult SemanticCompressor::decodeTier2(const std::vector<uint8_t>& data) {
    if (data.size() < 18) {
        throw std::runtime_error("Tier 2 payload too short (minimum 18 bytes required)");
    }
    SemanticResult res;
    res.compressionTier = CompressionTier::TIER_2_STRUCTURED;
    res.isFallback = false;
    res.isNegated = ((data[0] & 0x80) != 0) || ((data[12] & 0x01) != 0);

    res.intent  = static_cast<ActionCode>(data[1]);
    res.action  = static_cast<ActionCode>(data[2]);
    res.hazard  = static_cast<HazardCode>(data[3]);
    res.urgency = static_cast<UrgencyCode>(data[4]);

    res.personCount = (static_cast<uint32_t>(data[5]) << 8) | static_cast<uint32_t>(data[6]);

    uint16_t gid = (static_cast<uint16_t>(data[7]) << 8) | static_cast<uint16_t>(data[8]);
    res.location.geoId = gid;
    res.location.canonicalName = geoIdToString(gid);
    res.location.confidence = 0.95f;

    res.confidence = static_cast<float>(data[9]) / 100.0f;

    std::string lang;
    if (data[10] != 0) lang.push_back(static_cast<char>(data[10]));
    if (data[11] != 0) lang.push_back(static_cast<char>(data[11]));
    res.detectedLanguage = lang.empty() ? "en" : lang;

    return res;
}

std::vector<uint8_t> SemanticCompressor::encodeTier3(const SemanticResult& res) {
    // Dynamic bounded Tier 3 layout: Header (3B) + text bytes (up to 33B) <= 36B
    constexpr size_t PAYLOAD_CAP = 33;
    const std::string& text = res.originalText;
    size_t copyBytes = std::min<size_t>(text.size(), PAYLOAD_CAP);

    std::vector<uint8_t> buf(3 + copyBytes, 0);
    buf[0] = static_cast<uint8_t>(CompressionTier::TIER_3_FALLBACK);
    buf[1] = static_cast<uint8_t>(copyBytes);
    buf[2] = 0x01; // Direct UTF-8 mode

    for (size_t i = 0; i < copyBytes; ++i) {
        buf[3 + i] = static_cast<uint8_t>(text[i]);
    }
    return buf;
}

SemanticResult SemanticCompressor::decodeTier3(const std::vector<uint8_t>& data) {
    if (data.size() < 3) {
        throw std::runtime_error("Tier 3 payload too short (minimum 3 bytes required)");
    }
    SemanticResult res;
    res.compressionTier = CompressionTier::TIER_3_FALLBACK;
    res.isFallback = true;
    res.fallbackReason = "Decoded from Tier 3 fallback payload";
    res.confidence = 0.50f;

    uint8_t textLen = data[1];
    size_t availableBytes = data.size() - 3;
    size_t actualLen = std::min<size_t>(static_cast<size_t>(textLen), availableBytes);

    std::string text(reinterpret_cast<const char*>(&data[3]), actualLen);
    res.originalText = text;
    return res;
}

std::vector<uint8_t> SemanticCompressor::compress(const SemanticResult& result) {
    switch (result.compressionTier) {
        case CompressionTier::TIER_1_MACRO:
            return encodeTier1(result);
        case CompressionTier::TIER_2_STRUCTURED:
            return encodeTier2(result);
        case CompressionTier::TIER_3_FALLBACK:
        default:
            return encodeTier3(result);
    }
}

SemanticResult SemanticCompressor::decompress(const std::vector<uint8_t>& payload) {
    if (payload.empty()) {
        throw std::invalid_argument("SemanticCompressor::decompress — received empty payload");
    }

    uint8_t tierHeader = payload[0];
    if (tierHeader == static_cast<uint8_t>(CompressionTier::TIER_1_MACRO)) {
        return decodeTier1(payload);
    } else if (tierHeader == static_cast<uint8_t>(CompressionTier::TIER_2_STRUCTURED)) {
        return decodeTier2(payload);
    } else if (tierHeader == static_cast<uint8_t>(CompressionTier::TIER_3_FALLBACK)) {
        return decodeTier3(payload);
    } else {
        // Unknown tier header — attempt safe fallback
        SemanticResult res;
        res.isFallback = true;
        res.fallbackReason = "Unknown tier header: " + std::to_string(tierHeader);
        res.compressionTier = CompressionTier::TIER_3_FALLBACK;
        return res;
    }
}

} // namespace itantra::semantic
