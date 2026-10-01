# Member 3 — Semantic Compression & TinyML Agent

**Project:** iTantra / SIH 2026  
**Module:** Member 3 — Semantic Compression & TinyML Agent Lead  

---

## 1. System Overview

Member 3 operates directly between the **Speech-to-Text (STT)** pipeline (Member 2) and the **Wireless Transport Layer** (Member 4). It is responsible for semantic parsing, intent extraction, local geographic entity resolution, vocal urgency classification, 3-tier semantic payload compression, and Protobuf binary framing with CRC16 error validation.

```text
Transmitter Flow:
  STT Transcript
        ↓
  TinyML Semantic Analysis (tinyml_agent.py)
        ↓
  SemanticResult
        ↓
  3-Tier Semantic Compression (semantic_compressor.py)
        ↓
  Protobuf + CRC16 Framing (packet_framer.py)
        ↓
  Serialized Binary Packet
        ↓
  Member 4 / Network Transport Layer

Receiver Flow:
  Network Packet (bytes)
        ↓
  CRC16 Checksum Validation (packet_framer.py)
        ↓
  Protobuf Frame Decoding (packet_schema_pb2.py)
        ↓
  Semantic Payload Decompression (semantic_compressor.py)
        ↓
  Translation / Semantic Realization (translation_engine.py)
        ↓
  TTS Synthesizer (Member 2)
```

---

## 2. Problem Being Solved

In tactical, disaster response, and offline low-bandwidth communication scenarios, transmitting raw speech audio waveforms or even compressed audio features consumes excessive channel capacity and is prone to packet loss.

### The Member 3 Approach

Instead of sending raw audio frames, speech is transcribed to text locally by STT, and Member 3 extracts the underlying structured semantic information.

For example, the transcript:
> *"Five people are trapped near Tolankere because of flooding."*

is converted into a structured semantic representation:
- **`person_count`**: `5`
- **`location`**: `Tolankere` (GeoID: `1001`)
- **`hazard`**: `FLOOD` (HazardCode: `1`)
- **`urgency`**: `CRITICAL_SOS` (UrgencyCode: `3`)

This structured information is compressed into compact binary representations (6 to 38 bytes), allowing critical emergency data to transmit over ultra-low-bitrate radio links.

---

## 3. Tokenization vs. Semantic Compression

It is vital to distinguish NLP tokenization from semantic compression:

### NLP Tokenization
Converts raw text into token IDs or subword indices (e.g., using `tinyml_v3_tokenizer.json`) for neural network input processing. Tokenization is a preprocessing step for inference—not a payload reduction mechanism for wireless transport.

### Semantic Compression
Extracts conceptual meaning (intent, hazard, urgency, count, location) and maps those concepts to dense bit fields or codebook indices defined in `semantic_codebook.py`.

```text
Natural Language Input:
"Five people are trapped near Tolankere because of flooding."

Extracted Semantic Representation:
- Action: RESCUE (1)
- Hazard: FLOOD (1)
- Urgency: CRITICAL_SOS (3)
- Location: Tolankere (1001)
- Person Count: 5

Binary Output: Packed into 6–22 bytes depending on compression tier.
```

---

## 4. TinyML Agent (`tinyml_agent.py`)

The `TinyMLAgent` is the core semantic analyzer. It combines a model-backed classifier with a deterministic keyword/regex fallback to guarantee high availability in edge conditions.

### Model-Backed Classifier
- Uses quantized INT8 TFLite model (`tinyml_model_v3_int8.tflite`) with `tinyml_v3_tokenizer.json`.
- Predicts multi-task outputs for Intent, Action, Hazard, and Urgency.
- Also supports the fallback `tinyml_model.joblib` scikit-learn classifier if TFLite runtime dependencies are unavailable.

### Deterministic Keyword & Regex Fallback
- Triggered automatically if model inference fails, confidence falls below threshold, or model files are missing.
- Uses pattern matching for hazard identification (e.g., "flood", "fire", "quake"), numerical extraction ("5 people", "three persons"), and urgency keywords ("SOS", "trapped", "immediate").

---

## 5. Semantic Result (`SemanticResult`)

The output of `TinyMLAgent.analyze()` is a `SemanticResult` object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `intent` | `IntentCode` | High-level communication intent (e.g., `REPORT`, `REQUEST`, `ALERT`) |
| `action` | `ActionCode` | Required action (e.g., `RESCUE`, `EVACUATE`, `MEDICAL_AID`) |
| `hazard` | `HazardCode` | Identified hazard (e.g., `FLOOD`, `FIRE`, `EARTHQUAKE`, `LANDSLIDE`) |
| `urgency` | `UrgencyCode` | Urgency tier (`ROUTINE`, `TACTICAL`, `CRITICAL_SOS`) |
| `person_count` | `int` | Extracted count of affected individuals (0–255) |
| `location` | `str` | Resolved location string |
| `geo_id` | `int` | Codebook integer ID for resolved location |
| `detected_language` | `str` | BCP-47 language code (e.g., `"en"`, `"hi"`) |
| `confidence` | `float` | Model/inference confidence score (0.0 to 1.0) |
| `prosody_vector` | `bytes` | 16-byte prosodic feature vector |
| `compression_tier` | `CompressionTier` | Selected tier (`MACRO_T1`, `STRUCTURED_T2`, `FALLBACK_T3`) |
| `is_fallback` | `bool` | True if deterministic rules were used instead of ML |

---

## 6. Codebook (`semantic_codebook.py`)

The codebook maps semantic concepts to compact integer representations:

- **`ActionCode`**: `UNKNOWN (0)`, `RESCUE (1)`, `EVACUATE (2)`, `MEDICAL_AID (3)`, `FOOD_WATER (4)`, `ROAD_BLOCK (5)`
- **`HazardCode`**: `UNKNOWN (0)`, `FLOOD (1)`, `FIRE (2)`, `EARTHQUAKE (3)`, `LANDSLIDE (4)`, `CYCLONE (5)`
- **`UrgencyCode`**: `ROUTINE (1)`, `TACTICAL (2)`, `CRITICAL_SOS (3)`
- **`CompressionTier`**: `MACRO_T1 (1)`, `STRUCTURED_T2 (2)`, `FALLBACK_T3 (3)`
- **`GeoID`**: Pre-mapped regional locations (e.g., `1001: Tolankere`, `1002: Hubbli`, `1003: Dharwad`)

---

## 7. Geo Resolver (`geo_resolver.py`)

Speech-to-Text outputs often suffer from phonetic misspellings or regional accent variations (e.g., `"Tolan care"` instead of `"Tolankere"`, `"hubly"` instead of `"Hubbli"`).

`GeoResolver` implements:
- **Phonetic Matching (Soundex)**: Converts location strings into phonetic codes to match noisy STT outputs.
- **Prefix Trie & Levenshtein Distance**: Matches partial strings and typos to known geographic entities.

Example Supported Resolutions:
- `"Tolan care"` → `"Tolankere"` (GeoID: `1001`)
- `"hubly"` → `"Hubbli"` (GeoID: `1002`)

---

## 8. Three-Tier Compression (`semantic_compressor.py`)

Member 3 implements a 3-tier adaptive compression scheme:

| Tier | Name | Target Payload Size | Description |
|------|------|--------------------|-------------|
| **Tier 1** | **Macro** | **6–8 bytes** | Highly structured emergency alerts. Encodes Action, Hazard, Urgency, Person Count, and GeoID into compact binary bitfields. |
| **Tier 2** | **Structured** | **18–22 bytes** | Includes Tier 1 fields plus extended attributes such as fine-grained GPS offsets, status flags, and prosodic markers. |
| **Tier 3** | **Fallback** | **35–38 bytes** | Used when input transcript cannot be mapped to predefined codebook entries. Encodes bounded/truncated UTF-8 text with basic header metadata. |

> [!WARNING]  
> **Tier 3 Limitation:** Tier 3 uses truncated UTF-8 fallback text. It is **not** lossless for long arbitrary text messages exceeding payload boundaries.

---

## 9. Protobuf Packet Framing & Serialization (`packet_framer.py`)

The binary packet format is defined in `proto/packet_schema.proto` and compiled into `packet_schema_pb2.py`.

### VoicePacket Schema Fields:
- `magic_header`: `0x4954` (`"IT"`)
- `sequence_number`: `uint32`
- `timestamp_ms`: `uint64`
- `priority`: `int32`
- `source_callsign`: `string`
- `source_language`: `string`
- `compressed_payload`: `bytes`
- `prosody_vector`: `bytes` (16 bytes)
- `crc16_checksum`: `uint32`

---

## 10. CRC16 Integrity Check

Packet framing appends a **CRC16-CCITT** checksum computed over the frame bytes (excluding the checksum field itself).

> [!IMPORTANT]  
> CRC16 provides **error detection and payload integrity verification** over lossy transmission channels. It does **NOT** provide encryption or security.

---

## 11. Prosody Vector

`m3_integration.py` supports carrying a 16-byte `prosody_vector` representing acoustic/prosodic markers (pitch, energy, speaking rate) alongside the compressed semantic packet. This allows the receiver's TTS engine (Member 2) to reconstruct voice emotion and urgency.

---

## 12. Translation Engine (`translation_engine.py`)

The receiver side uses `translation_engine.py` to realize the decoded `SemanticResult` into target Indic languages before TTS synthesis.

### Currently Supported Target Languages:
- English (`"en"`)
- Hindi (`"hi"`)
- Tamil (`"ta"`)
- Kannada (`"kn"`)
- Marathi (`"mr"`)
- Telugu (`"te"`)

Example: A Tier 1 payload sent from English transcript `"Five people trapped near Tolankere because of flooding"` decompressed at receiver with `target_language="hi"` realizes to:
> `"Tolankere में FLOOD के कारण emergency स्थिति है। RESCUE सहायता की आवश्यकता है।"`

---

## 13. Public Integration API (`m3_integration.py`)

`m3_integration.py` provides the official entry point for external modules:

```python
from m3_integration import process_transcript, decode_packet

# 1. Transmitter Side: Process transcript and build binary frame
packet = process_transcript(
    transcript="Five people are trapped near Tolankere because of flooding.",
    source_language="en",
    target_language="hi",
    prosody_vector=bytes(16),
    callsign="RESCUE_01",
    sequence=101,
    priority=-1
)

wire_bytes = packet.serialized_bytes
print(f"Wire bytes ({len(wire_bytes)} bytes): {wire_bytes.hex()}")

# 2. Receiver Side: Validate frame, decompress, and realize text
decoded = decode_packet(
    wire_bytes=wire_bytes,
    target_language="hi"
)

print(f"CRC Valid: {decoded.crc_valid}")
print(f"Decoded Text ({decoded.target_language}): {decoded.decoded_text}")
```

---

## 14. Network Integration Contract (Member 4 Boundary)

```text
Member 3 (Transmitter) ──[ serialized bytes ]──> Member 4 (Network Transport)
                                                          │
                                                          ▼ (Wireless Link)
                                                          │
Member 3 (Receiver)    <──[ serialized bytes ]─── Member 4 (Network Transport)
```

Member 3 delivers raw binary bytes (`packet.serialized_bytes`) to Member 4 for transmission, and accepts raw binary bytes (`wire_bytes`) from Member 4 for reception and decoding.

---

## 15. Testing Suite

The complete Member 3 test suite is located in `test_member3_suite.py`.

### Running Tests:
```bash
PYTHONPATH=web-demo/backend python test_member3_suite.py
```

### Test Coverage (8 / 8 PASSED):
1. `test_tier1_macro_emergency`: Verifies Tier 1 macro emergency compression and framing.
2. `test_tier2_structured_emergency`: Verifies Tier 2 structured payload compression.
3. `test_tier3_fallback`: Verifies Tier 3 fallback text handling.
4. `test_multilingual_hindi_realization`: Verifies Hindi text realization from semantic result.
5. `test_roundtrip_with_prosody`: Verifies 16-byte prosody vector preservation across round-trip.
6. `test_crc_corruption_rejection`: Verifies rejection of corrupted frame bytes.
7. `test_payload_boundaries`: Verifies behavior under max payload sizes.
8. `test_phonetic_geo_matching`: Verifies phonetic resolution of `"Tolan care"` to `"Tolankere"`.

---

## 16. Known Integration & Architectural Notes

### Dual Processing Paths in Codebase:
1. **Path A (`main.py`)**: Used by web demo server (`semantic_parser.py` → `hybrid_engine.py` → `tinyml_classifier.py` → `semantic_compressor.py`).
2. **Path B (`m3_integration.py`)**: Standard Member 3 pipeline (`m3_integration.py` → `tinyml_agent.py` → `SemanticResult` → `semantic_compressor.py`).

> [!NOTE]  
> Path A uses `SemanticMessage` objects whereas Path B and the new `semantic_compressor.py` use `SemanticResult`. Full unified end-to-end integration will standardize all paths on `SemanticResult`.

---

## 17. Member 3 Directory Structure

```text
web-demo/backend/
├── m3_integration.py          # Primary public integration interface
├── tinyml_agent.py            # Multi-task TinyML agent classifier & fallback
├── semantic_compressor.py     # 3-tier semantic compression & decompression
├── semantic_codebook.py       # Codebook definitions (Action, Hazard, Urgency, Geo)
├── geo_resolver.py            # Phonetic (Soundex) & Trie geographic entity resolver
├── packet_framer.py           # Protobuf packet framing & CRC16 calculation
├── translation_engine.py      # Indic semantic text realization engine
├── semantic_schema.py         # Legacy schema definitions & compatibility
├── packet_schema_pb2.py       # Protobuf generated Python bindings
├── tinyml_model.joblib        # Scikit-learn fallback model
├── tinyml_model_v3_int8.tflite# Quantized INT8 TinyML TFLite classifier
└── tinyml_v3_tokenizer.json   # Subword tokenizer vocabulary for TinyML model

proto/
└── packet_schema.proto        # Protobuf schema definition

src/
├── Member3Integration.cpp     # C++ Member 3 core implementation
├── TinyMLAgent.cpp            # C++ TinyML agent
├── SemanticCompressor.cpp     # C++ 3-tier compressor
├── PacketFramer.cpp           # C++ packet framer
├── GeoResolver.cpp            # C++ geo resolver
└── tests_member3.cpp          # C++ test suite
```

---

## 18. Implementation Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| **Semantic Codebook** | Implemented | Enums for Action, Hazard, Urgency, GeoID defined in `semantic_codebook.py` |
| **TinyML Agent** | Implemented | INT8 TFLite model with regex/keyword fallback in `tinyml_agent.py` |
| **GeoResolver** | Implemented | Soundex & Trie phonetic matching in `geo_resolver.py` |
| **Tier 1 Macro Compression** | Implemented | 6–8 byte binary payload compression |
| **Tier 2 Structured Compression** | Implemented | 18–22 byte binary payload compression |
| **Tier 3 Fallback Compression** | Implemented | 35–38 byte bounded UTF-8 text fallback |
| **Protobuf Packet Framing** | Implemented | Protobuf schema `packet_schema.proto` + Python bindings |
| **CRC16 Validation** | Implemented | CRC16-CCITT checksum validation in `packet_framer.py` |
| **Translation Engine** | Implemented | Semantic realization for EN, HI, TA, KN, MR, TE |
| **Integration API** | Implemented | `process_transcript()` & `decode_packet()` in `m3_integration.py` |
| **Test Suite** | Passing | 8/8 tests passed in `test_member3_suite.py` |
| **Member 4 Interface** | Defined | Binary bytes interface contract ready |
| **C++ Core Engine** | Implemented | Native C++ sources in `src/` directory |
