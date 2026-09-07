#include "SemanticCodebook.hpp"
#include <algorithm>

namespace itantra::semantic {

std::string actionToString(ActionCode code) {
    switch (code) {
        case ActionCode::RESCUE_REQUEST:  return "RESCUE_REQUEST";
        case ActionCode::EVACUATE:        return "EVACUATE";
        case ActionCode::MEDICAL:         return "MEDICAL";
        case ActionCode::SUPPLIES:        return "SUPPLIES";
        case ActionCode::SEARCH:          return "SEARCH";
        case ActionCode::REPORT:          return "REPORT";
        case ActionCode::FLOOD:           return "FLOOD";
        case ActionCode::BOAT:            return "BOAT";
        case ActionCode::FIRE:            return "FIRE";
        case ActionCode::SOS:             return "SOS";
        case ActionCode::PERSON_MISSING:  return "PERSON_MISSING";
        case ActionCode::LOCATION_REPORT: return "LOCATION_REPORT";
        case ActionCode::ALERT:           return "ALERT";
        case ActionCode::SECURE:          return "SECURE";
        case ActionCode::MOVE:            return "MOVE";
        case ActionCode::SEND_TEAM:       return "SEND_TEAM";
        case ActionCode::REQUEST_HELP:    return "REQUEST_HELP";
        case ActionCode::CANCEL:          return "CANCEL";
        case ActionCode::HOLD:            return "HOLD";
        case ActionCode::RESPOND:         return "RESPOND";
        default:                          return "UNKNOWN";
    }
}

ActionCode stringToAction(std::string_view name) {
    if (name == "RESCUE_REQUEST") return ActionCode::RESCUE_REQUEST;
    if (name == "EVACUATE")       return ActionCode::EVACUATE;
    if (name == "MEDICAL")        return ActionCode::MEDICAL;
    if (name == "SUPPLIES")       return ActionCode::SUPPLIES;
    if (name == "SEARCH")         return ActionCode::SEARCH;
    if (name == "REPORT")         return ActionCode::REPORT;
    if (name == "FLOOD")          return ActionCode::FLOOD;
    if (name == "BOAT")           return ActionCode::BOAT;
    if (name == "FIRE")           return ActionCode::FIRE;
    if (name == "SOS")            return ActionCode::SOS;
    if (name == "PERSON_MISSING") return ActionCode::PERSON_MISSING;
    if (name == "LOCATION_REPORT")return ActionCode::LOCATION_REPORT;
    if (name == "ALERT")          return ActionCode::ALERT;
    if (name == "SECURE")         return ActionCode::SECURE;
    if (name == "MOVE")           return ActionCode::MOVE;
    if (name == "SEND_TEAM")      return ActionCode::SEND_TEAM;
    if (name == "REQUEST_HELP")   return ActionCode::REQUEST_HELP;
    if (name == "CANCEL")         return ActionCode::CANCEL;
    if (name == "HOLD")           return ActionCode::HOLD;
    if (name == "RESPOND")        return ActionCode::RESPOND;
    return ActionCode::UNKNOWN;
}

std::string urgencyToString(UrgencyCode code) {
    switch (code) {
        case UrgencyCode::ROUTINE:      return "ROUTINE";
        case UrgencyCode::TACTICAL:     return "TACTICAL";
        case UrgencyCode::CRITICAL_SOS: return "CRITICAL_SOS";
        default:                        return "ROUTINE";
    }
}

UrgencyCode stringToUrgency(std::string_view name) {
    if (name == "TACTICAL")     return UrgencyCode::TACTICAL;
    if (name == "CRITICAL_SOS" || name == "CRITICAL" || name == "HIGH") return UrgencyCode::CRITICAL_SOS;
    return UrgencyCode::ROUTINE;
}

std::string hazardToString(HazardCode code) {
    switch (code) {
        case HazardCode::FLOOD:             return "FLOOD";
        case HazardCode::FIRE:              return "FIRE";
        case HazardCode::EARTHQUAKE:        return "EARTHQUAKE";
        case HazardCode::LANDSLIDE:         return "LANDSLIDE";
        case HazardCode::BUILDING_COLLAPSE: return "BUILDING_COLLAPSE";
        case HazardCode::EXPLOSION:         return "EXPLOSION";
        case HazardCode::GAS_LEAK:          return "GAS_LEAK";
        case HazardCode::STORM:             return "STORM";
        case HazardCode::GENERAL_DANGER:    return "GENERAL_DANGER";
        default:                            return "NONE";
    }
}

HazardCode stringToHazard(std::string_view name) {
    if (name == "FLOOD")             return HazardCode::FLOOD;
    if (name == "FIRE")              return HazardCode::FIRE;
    if (name == "EARTHQUAKE")        return HazardCode::EARTHQUAKE;
    if (name == "LANDSLIDE")         return HazardCode::LANDSLIDE;
    if (name == "BUILDING_COLLAPSE") return HazardCode::BUILDING_COLLAPSE;
    if (name == "EXPLOSION")         return HazardCode::EXPLOSION;
    if (name == "GAS_LEAK")          return HazardCode::GAS_LEAK;
    if (name == "STORM")             return HazardCode::STORM;
    if (name == "GENERAL_DANGER")    return HazardCode::GENERAL_DANGER;
    return HazardCode::NONE;
}

std::string geoIdToString(uint16_t geoId) {
    switch (geoId) {
        case GeoID::TOLANKERE: return "Tolankere";
        case GeoID::HUBBLI:    return "Hubbli";
        case GeoID::BASE:      return "Base Camp";
        case GeoID::SECTOR_1:  return "Sector 1";
        case GeoID::SECTOR_2:  return "Sector 2";
        case GeoID::SECTOR_3:  return "Sector 3";
        case GeoID::SECTOR_4:  return "Sector 4";
        case GeoID::SECTOR_5:  return "Sector 5";
        case GeoID::BRIDGE:    return "Bridge";
        case GeoID::HOSPITAL:  return "Hospital";
        case GeoID::SCHOOL:    return "School";
        default:               return "Unknown Location";
    }
}

uint16_t stringToGeoId(std::string_view name) {
    if (name == "Tolankere" || name == "tolankere") return GeoID::TOLANKERE;
    if (name == "Hubbli" || name == "hubbli" || name == "hubli") return GeoID::HUBBLI;
    if (name == "Base Camp" || name == "Base" || name == "base") return GeoID::BASE;
    if (name == "Sector 1" || name == "sector 1") return GeoID::SECTOR_1;
    if (name == "Sector 2" || name == "sector 2") return GeoID::SECTOR_2;
    if (name == "Sector 3" || name == "sector 3") return GeoID::SECTOR_3;
    if (name == "Sector 4" || name == "sector 4") return GeoID::SECTOR_4;
    if (name == "Sector 5" || name == "sector 5") return GeoID::SECTOR_5;
    if (name == "Bridge" || name == "bridge") return GeoID::BRIDGE;
    if (name == "Hospital" || name == "hospital") return GeoID::HOSPITAL;
    if (name == "School" || name == "school") return GeoID::SCHOOL;
    return GeoID::UNKNOWN;
}

std::string compressionTierToString(CompressionTier tier) {
    switch (tier) {
        case CompressionTier::TIER_1_MACRO:      return "Tier 1 (Macro, 6-8B)";
        case CompressionTier::TIER_2_STRUCTURED: return "Tier 2 (Structured, 18-22B)";
        case CompressionTier::TIER_3_FALLBACK:   return "Tier 3 (Fallback, 35-38B)";
        default:                                 return "Unknown Tier";
    }
}

} // namespace itantra::semantic
