#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include "SemanticCodebook.hpp"

namespace itantra::semantic {

struct LocationEntity {
    std::string canonicalName;
    uint16_t geoId = GeoID::UNKNOWN;
    float confidence = 0.0f;
    std::string matchedToken;
};

struct LandmarkEntry {
    std::string canonicalName;
    uint16_t geoId;
    std::vector<std::string> aliases;
    std::vector<std::string> phoneticAliases;
};

class GeoResolver {
public:
    GeoResolver();

    /// Resolve geographic entities in text using phonetic + approximate matching.
    /// @param text Input natural language or location phrase
    /// @return LocationEntity with canonicalName, geoId, and confidence
    LocationEntity resolveLocation(const std::string& text) const;

    /// Add a landmark dynamically to the offline database
    void registerLandmark(const std::string& canonicalName, uint16_t geoId,
                          const std::vector<std::string>& aliases = {});

    /// Soundex phonetic code calculation (English / Romanized)
    static std::string computeSoundex(const std::string& word);

    /// Levenshtein edit distance between two strings
    static int levenshteinDistance(const std::string& s1, const std::string& s2);

    /// Calculate string similarity ratio between 0.0 and 1.0
    static float similarityRatio(const std::string& s1, const std::string& s2);

private:
    std::vector<LandmarkEntry> landmarks_;
    void initializeDefaultLandmarks();
    static std::string normalize(const std::string& input);
};

} // namespace itantra::semantic
