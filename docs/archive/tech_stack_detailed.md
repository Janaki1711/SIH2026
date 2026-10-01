# iTantra Complete Technology Stack (Ultra-Detailed Specification)

---

## 📱 1. APPLICATION & MOBILE FRAMEWORK LAYER
* **Language & Runtime**: Kotlin 1.9.20 with Java 17 Bytecode Target.
* **Target Android Version**: Android 8.0 (API Level 26) minimum up to Android 14 (API Level 34).
* **Architecture Pattern**: MVVM (Model-View-ViewModel) + Clean Architecture with Repository pattern.
* **Asynchronous Concurrency**: Kotlin Coroutines (`Dispatchers.IO`, `Dispatchers.Main`), Flow APIs, StateFlow, Channels.
* **UI & Layout Components**: Material Design 3, RecyclerView with custom WhatsApp-style chat adapters (`ChatAdapter.kt`), ConstraintLayout, FrameLayout, Dynamic Diagnostic Canvas.
* **Local Persistence**: Room Database 2.6.1 (SQLite Driver), SharedPreferences, Encrypted SharedPreferences.

---

## ⚡ 2. LOW-LATENCY NATIVE C++ NDK LAYER
* **Native Language Standard**: C++20 (Clang toolchain in Android NDK r26b).
* **Native JNI Bridge**: JNI Bridge (`NativeSTTBridge.cpp`, `SemanticBridge.cpp`) connecting Kotlin to NDK core.
* **Audio Engine**: Google Oboe Audio API 1.8.0 (High-performance C++ wrapper over AAudio and OpenSL ES).
* **Audio Stream Config**: $16\text{ kHz}$ sampling rate, 16-bit PCM Mono, $20\text{ ms}$ buffer size ($320\text{ samples/frame}$), `AAUDIO_PERFORMANCE_MODE_LOW_LATENCY`.

---

## 🔍 3. VOICE ACTIVITY DETECTION (VAD) ENGINE
* **VAD Model Architecture**: Silero VAD (512-sample / 32 ms chunks, speech gate 0.25; no version string in shipped ONNX).
* **Execution Engine**: ONNX Runtime C++ API 1.16.3 (`libonnxruntime.so`).
* **Model Footprint**: $2.3\text{ MB}$ ONNX binary (`silero_vad.onnx` = 2,327,524 B).
* **Operational Spec**: Evaluates $30\text{ ms}$ PCM audio chunks; triggers sentence boundary after $300\text{ ms}$ continuous silence; $<0.05\text{ ms}$ CPU evaluation time per chunk.

---

## 🤖 4. SPEECH-TO-TEXT (STT) ENGINE & AI MODELS
* **Primary Dravidian/Indic Model**: `parambharat/whisper-tiny-south-indic` (GGML Q8_0 8-bit quantized binary, $43.5\text{ MB}$).
* **Fine-Tuning Datasets**: **$1,700\text{ Hours}$ Kathbath** + **$7,000\text{ Hours}$ Vaani** multilingual Indic speech datasets (AI4Bharat, IIT Madras).
* **Secondary Conformer Engine**: `IndicConformer` ONNX model (`encoder.onnx`, $197\text{ MB}$).
* **Feature Extraction**: 80-channel log-mel filterbank spectrogram computation in C++; SIMD INT8 vectorized execution.

---

## 🌐 5. TRANSLATION & TRANSLITERATION ENGINE
* **Structural Pattern Engine**: `translatePattern()` matching name introductions and disaster phrases across all 11 languages (`"My name is X"`, `"ನನ್ನ ಹೆಸರು X"`, `"मेरा नाम X"`, `"నా పేరు X"`, `"என் பெயர் X"`, `"എന്റെ പേര് X"`, `"माझे नाव X"`, `"আমার নাম X"`, `"મારું નામ X"`, `"ମୋର ନାମ X"`, `"ਮੇਰਾ ਨਾਂ X"`).
* **Parallel Indic Unicode Engine**: `PivotTranslator` 10-language Unicode offset mapping (`0x0900` Devanagari, `0x0980` Bengali, `0x0A00` Gurmukhi, `0x0A80` Gujarati, `0x0B00` Odia, `0x0B80` Tamil, `0x0C00` Telugu, `0x0C80` Kannada, `0x0D00` Malayalam).
* **Neural Cascade Engine**: Google ML Kit Translate API (`TranslateLanguage` on-device models with English pivot fallback).

---

## 🗣️ 6. SPEECH SYNTHESIS (TTS) ENGINE
* **Primary Synthesizer**: Indic TTS Engine / eSpeak-NG NDK engine with native prosody synthesis.
* **Platform Fallback Engine**: Android Native `TextToSpeech` Engine (`android.speech.tts.TextToSpeech`).
* **Audio Dynamics**: Custom pitch and speed controllers; Automatic Volume Override for Emergency Broadcasts (forces $100\%$ system volume and overrides silent/DND mode).

---

## 📶 7. DECENTRALIZED WIRELESS MESH & NETWORKING PROTOCOL
* **Primary Link Protocol**: Wi-Fi Direct (P2P Group Owner Topology, IEEE 802.11a/b/g/n/ac, $80\text{–}120\text{ m}$ LOS range).
* **Secondary Link Protocol**: Bluetooth Low Energy (BLE) / L2CAP Socket Fallback.
* **Transport Layer**: Custom Binary UDP Multicast / Unicast Datagram Sockets via `WfbngManager.kt`.
* **Channel Management**: Time-Division Sender Queue + Channel Collision Avoidance (unique SenderID headers).
* **Binary Packet Framing**:
  `[Wfbng hdr: 40B = magic 1 | ttl 1 | seq 2 | origin 16 | target 16 | shard 2 | len 2] + [RS shard: 10B]`

---

## 🔐 8. SECURITY, RELIABILITY & DATA INTEGRITY
* **AEAD Encryption Cipher (PRIMARY)**: **ChaCha20-Poly1305 AEAD** (RFC 7539 / Conscrypt implementation via `ChaCha20Poly1305Engine.kt`) — High-speed stream cipher optimized for mobile CPUs without hardware AES acceleration.
* **Encryption Cipher (FALLBACK)**: ChaCha20-Poly1305 AEAD (primary); AES-256-GCM fallback (32-byte key).
* **Forward Error Correction (FEC)**: Reed-Solomon Code $(255, 223)$ — recovers up to $16$ lost bytes per packet over noisy RF links.
* **Checksum Verification**: Poly1305 AEAD tag — no CRC in the TX path (CRC16-CCITT exists only in the unwired PacketFramer).
