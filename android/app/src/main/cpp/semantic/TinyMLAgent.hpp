#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include "SemanticCodebook.hpp"
#include "GeoResolver.hpp"

namespace itantra::semantic {

struct ExtractedEntity {
    std::string key;
    std::string value;
    float confidence = 1.0f;
};

struct SemanticResult {
    std::string originalText;
    std::string detectedLanguage = "en";
    ActionCode intent = ActionCode::UNKNOWN;
    ActionCode action = ActionCode::UNKNOWN;
    HazardCode hazard = HazardCode::NONE;
    LocationEntity location;
    uint32_t personCount = 0;
    UrgencyCode urgency = UrgencyCode::ROUTINE;
    float confidence = 1.0f;
    CompressionTier compressionTier = CompressionTier::TIER_1_MACRO;
    std::vector<ExtractedEntity> extractedEntities;
    bool isFallback = false;
    bool isNegated = false;
    // True only for decline/cancel-class negation ("do not need", "వద్దు",
    // "बೇಡ"...). Bare absence ("no water", "నీరు లేదు") leaves this false so
    // realize() renders the POSITIVE need instead of a "NOT required"
    // cancellation. Absence of a resource in a disaster report means it is
    // needed — only an explicit decline cancels.
    bool isStrongNegation = false;
    std::string fallbackReason;
    std::vector<uint8_t> prosodyVector; // 16 bytes if present
    std::string modelBackendUsed = "DETERMINISTIC_FALLBACK"; // Clearly label backend
};

/// Interface for ML-backed inference (e.g., INT8 IndicBERT-Tiny / MobileBERT)
class ITinyMLSemanticModel {
public:
    virtual ~ITinyMLSemanticModel() = default;
    virtual bool isModelLoaded() const = 0;
    virtual std::string getModelName() const = 0;
    virtual bool runInference(const std::string& text, const std::string& language, SemanticResult& outResult) = 0;
};

/// Multi-Task TinyML Agent managing local entity resolution, semantic extraction, and triage
class TinyMLAgent {
public:
    TinyMLAgent();
    explicit TinyMLAgent(std::shared_ptr<ITinyMLSemanticModel> mlModel);

    /// Set or update the ML inference backend
    void setModelBackend(std::shared_ptr<ITinyMLSemanticModel> mlModel);

    /// Process an STT transcript and extract structured semantic understanding
    /// @param text The input STT transcript
    /// @param sourceLanguage Language tag (e.g. "hi", "kn", "ta", "mr", "en")
    /// @param optionalProsody Optional 16-byte prosody vector
    /// @return Complete SemanticResult
    SemanticResult analyze(const std::string& text,
                           const std::string& sourceLanguage = "en",
                           const std::vector<uint8_t>& optionalProsody = {});

    /// Classify vocal urgency from textual cues and optional acoustic parameters
    static UrgencyCode classifyUrgency(const std::string& text,
                                       ActionCode intent,
                                       HazardCode hazard,
                                       const std::vector<uint8_t>& acousticProsody = {});

    /// Access the internal GeoResolver
    const GeoResolver& getGeoResolver() const { return geoResolver_; }
    GeoResolver& getGeoResolver() { return geoResolver_; }

private:
    std::shared_ptr<ITinyMLSemanticModel> mlModel_;
    GeoResolver geoResolver_;

    SemanticResult runDeterministicFallback(const std::string& text,
                                            const std::string& sourceLanguage,
                                            const std::vector<uint8_t>& prosody);

    static uint32_t extractPersonCount(const std::string& text);
    static bool extractNegation(const std::string& text);
    static bool extractStrongNegation(const std::string& text);
    static ActionCode extractActionAndIntent(const std::string& text, ActionCode& outAction);
    static HazardCode extractHazard(const std::string& text);
    static std::string detectLanguage(const std::string& text, const std::string& fallbackLang);
};

} // namespace itantra::semantic
