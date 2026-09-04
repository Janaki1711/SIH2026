#pragma once

#include <string>
#include <vector>
#include <memory>
#include "TinyMLAgent.hpp"

namespace itantra::translation {

class ITranslationModel {
public:
    virtual ~ITranslationModel() = default;
    virtual bool isLoaded() const = 0;
    virtual std::string getModelName() const = 0;
    virtual std::string translate(const std::string& text,
                                  const std::string& sourceLang,
                                  const std::string& targetLang) = 0;
};

class TranslationBridge {
public:
    TranslationBridge();
    explicit TranslationBridge(std::shared_ptr<ITranslationModel> model);

    void setModel(std::shared_ptr<ITranslationModel> model);

    /// Realize a SemanticResult into human-readable target language text.
    /// @param result The decoded semantic result
    /// @param targetLanguage BCP-47 target tag ("hi", "ta", "kn", "mr", "te", "en")
    /// @return Realized natural language sentence
    std::string realize(const semantic::SemanticResult& result, const std::string& targetLanguage = "en");

    /// Direct text translation
    std::string translate(const std::string& text,
                          const std::string& sourceLanguage,
                          const std::string& targetLanguage);

private:
    std::shared_ptr<ITranslationModel> model_;

    std::string realizeEnglish(const semantic::SemanticResult& res);
    std::string realizeHindi(const semantic::SemanticResult& res);
    std::string realizeTamil(const semantic::SemanticResult& res);
    std::string realizeKannada(const semantic::SemanticResult& res);
    std::string realizeMarathi(const semantic::SemanticResult& res);
    std::string realizeTelugu(const semantic::SemanticResult& res);

    static std::string getTargetLocationName(uint16_t geoId, const std::string& lang);
};

} // namespace itantra::translation
