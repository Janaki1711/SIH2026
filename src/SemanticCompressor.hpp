#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include "SemanticCodebook.hpp"
#include "TinyMLAgent.hpp"

namespace itantra::semantic {

class SemanticCompressor {
public:
    /// Compress a SemanticResult into its target-tier binary representation.
    /// @param result The analyzed semantic understanding
    /// @return Compressed payload byte buffer (Tier 1: 6-8B, Tier 2: 18-22B, Tier 3: 35-38B)
    static std::vector<uint8_t> compress(const SemanticResult& result);

    /// Decompress a binary payload back into a SemanticResult.
    /// @param payload Compressed byte buffer
    /// @return Reconstructed SemanticResult
    static SemanticResult decompress(const std::vector<uint8_t>& payload);

    /// Encode Tier 1 (Semantic Macro: 6-8 bytes)
    static std::vector<uint8_t> encodeTier1(const SemanticResult& res);

    /// Decode Tier 1
    static SemanticResult decodeTier1(const std::vector<uint8_t>& data);

    /// Encode Tier 2 (Structured Frame: 18-22 bytes)
    static std::vector<uint8_t> encodeTier2(const SemanticResult& res);

    /// Decode Tier 2
    static SemanticResult decodeTier2(const std::vector<uint8_t>& data);

    /// Encode Tier 3 (Fallback: 35-38 bytes)
    static std::vector<uint8_t> encodeTier3(const SemanticResult& res);

    /// Decode Tier 3
    static SemanticResult decodeTier3(const std::vector<uint8_t>& data);
};

} // namespace itantra::semantic
