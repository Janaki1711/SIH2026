#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>

namespace itantra::semantic {

// ─────────────────────────────────────────────────────────────────────────────
// Semantic Action & Intent Codes (Centralized Codebook)
// ─────────────────────────────────────────────────────────────────────────────
enum class ActionCode : uint8_t {
    UNKNOWN          = 0x00,
    RESCUE_REQUEST   = 0x01,
    EVACUATE         = 0x02,
    MEDICAL          = 0x03,
    SUPPLIES         = 0x04,
    SEARCH           = 0x05,
    REPORT           = 0x06,
    FLOOD            = 0x07,
    BOAT             = 0x08,
    FIRE             = 0x09,
    SOS              = 0x0A,
    PERSON_MISSING   = 0x0B,
    LOCATION_REPORT  = 0x0C,
    ALERT            = 0x0D,
    SECURE           = 0x0E,
    MOVE             = 0x0F,
    SEND_TEAM        = 0x10,
    REQUEST_HELP     = 0x11,
    CANCEL           = 0x12,
    HOLD             = 0x13,
    RESPOND          = 0x14,
    // FIX 3: Navigation/movement intent
    GO_TO            = 0x15
};

// ─────────────────────────────────────────────────────────────────────────────
// Urgency Codes (Triage Level)
// ─────────────────────────────────────────────────────────────────────────────
enum class UrgencyCode : uint8_t {
    ROUTINE      = 0x00,
    TACTICAL     = 0x01,
    CRITICAL_SOS = 0x03
};

// ─────────────────────────────────────────────────────────────────────────────
// Hazard Codes
// ─────────────────────────────────────────────────────────────────────────────
enum class HazardCode : uint8_t {
    NONE              = 0x00,
    FLOOD             = 0x01,
    FIRE              = 0x02,
    EARTHQUAKE        = 0x03,
    LANDSLIDE         = 0x04,
    BUILDING_COLLAPSE = 0x05,
    EXPLOSION         = 0x06,
    GAS_LEAK          = 0x07,
    STORM             = 0x08,
    GENERAL_DANGER    = 0x09
};

// ─────────────────────────────────────────────────────────────────────────────
// Predefined Landmark GeoIDs (16-bit)
// ─────────────────────────────────────────────────────────────────────────────
namespace GeoID {
    constexpr uint16_t UNKNOWN                 = 0x0000;
    constexpr uint16_t TOLANKERE               = 0x4F2A;
    constexpr uint16_t HUBBLI                  = 0x4F2B;
    constexpr uint16_t KOLHAPUR                = 0x4F2C;
    constexpr uint16_t BENGALURU               = 0x4F2D;
    constexpr uint16_t BASE                    = 0x4F01;
    constexpr uint16_t SECTOR_1                = 0x4E01;
    constexpr uint16_t SECTOR_2                = 0x4E02;
    constexpr uint16_t SECTOR_3                = 0x4E03;
    constexpr uint16_t SECTOR_4                = 0x4E04;
    constexpr uint16_t SECTOR_5                = 0x4E05;
    constexpr uint16_t BRIDGE                  = 0x4E10;
    constexpr uint16_t HOSPITAL                = 0x4E11;
    constexpr uint16_t SCHOOL                  = 0x4E12;
    // FIX 3: Added missing location types
    constexpr uint16_t RAILWAY_STATION         = 0x4E13;
    constexpr uint16_t BUS_STAND               = 0x4E14;
    constexpr uint16_t AIRPORT                 = 0x4E15;
    constexpr uint16_t POLICE_STATION          = 0x4E16;
    constexpr uint16_t FIRE_STATION            = 0x4E17;
    constexpr uint16_t MARKET                  = 0x4E18;
    constexpr uint16_t TEMPLE                  = 0x4E19;
    constexpr uint16_t MOSQUE                  = 0x4E1A;
    constexpr uint16_t CHURCH                  = 0x4E1B;
    constexpr uint16_t HOME                    = 0x4E1C;
    constexpr uint16_t VILLAGE                 = 0x4E1D;
    constexpr uint16_t PROPER_LOCATION_DYNAMIC = 0x4FFF;
}

// ─────────────────────────────────────────────────────────────────────────────
// Compression Tier Enum
// ─────────────────────────────────────────────────────────────────────────────
enum class CompressionTier : uint8_t {
    TIER_1_MACRO      = 1, // 6–8 bytes
    TIER_2_STRUCTURED = 2, // 18–22 bytes
    TIER_3_FALLBACK   = 3  // 35–38 bytes
};

// ─────────────────────────────────────────────────────────────────────────────
// Helper String Conversion Utilities
// ─────────────────────────────────────────────────────────────────────────────
std::string actionToString(ActionCode code);
ActionCode stringToAction(std::string_view name);

std::string urgencyToString(UrgencyCode code);
UrgencyCode stringToUrgency(std::string_view name);

std::string hazardToString(HazardCode code);
HazardCode stringToHazard(std::string_view name);

std::string geoIdToString(uint16_t geoId);
uint16_t stringToGeoId(std::string_view name);

std::string compressionTierToString(CompressionTier tier);

} // namespace itantra::semantic
