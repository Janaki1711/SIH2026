# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Sponsoring Agency: Indian Space Research Organisation (ISRO)

> **Offline, Edge-Deployable, Multilingual Semantic Walkie-Talkie for Tactical, Disaster, and Ultra-Low-Bitrate Space/Radio Communications.**

---

## 🎯 Executive Summary & Core Principle

> **"Do not stream heavy raw audio over fragile, degraded wireless links — compress speech by 2,000× into semantic tokens on-device, transmit 40-byte micro-packets across physical distance, and synthesize natural speech locally."**

Standard voice streaming (Opus, PCM, AMR) requires **16 to 128 kbps**, collapsing completely under RF interference, satellite link bottlenecks, and disaster-induced infrastructure blackouts. **iTantra** implements **Semantic Voice Transmission (Voice → Text → RF → Voice)** directly on edge hardware, enabling **100% intelligible two-way communication at <50 bps** with zero cellular network or internet infrastructure.

---

## 🔄 End-to-End System Execution Flow

```
====================================================================================================
                                      SENDER PHONE (TRANSMITTER)
====================================================================================================

 [Step 1: User Presses PTT / Speaks]
    │
    ▼
 [Step 2: Google Oboe Audio Capture (C++ NDK)]
    │   • Captures raw 16kHz 16-bit Mono PCM audio in 30ms lock-free chunks (480 samples).
    ▼
 [Step 3: Silero VAD Gatekeeper (<1ms)]
    │   • Detects human voice onset and cutoff.
    │   • Gates subsequent heavy AI models so they sleep during silence (<3% idle CPU).
    ▼
 [Step 4: AI4Bharat IndicConformer STT Engine (INT8 ONNX)]
    │   • Processes the captured speech audio segment.
    │   • Outputs raw text transcript: "सेक्टर 4 में तुरंत मदद भेजो" + Language ID ("hi").
    ▼
 [Step 5: Prosody & Voice Feature Extractor]
    │   • Extracts 16-byte vector containing pitch contour (F0) + speaker timbre + urgency flag.
    ▼
 [Step 6: Arithmetic Tokenizer & Protobuf Framer]
    │   • Compresses UTF-8 text down to 22 bytes.
    │   • Packages binary frame: [Header | Priority: SOS | Lang: HI | Prosody | Payload | CRC16].
    │   • Total packet size: 38 Bytes!
    ▼
 [Step 7: Local Database Insertion (Room / SQLite)]
    │   • Logs message in local SQLite database with status "TRANSMITTING".
    ▼
 [Step 8: P2P Socket Transmitter]
    │   • Transmits 38 bytes over Wi-Fi Direct (or Bluetooth RFCOMM fallback).
    │
═════════════════════════════════════ WIRELESS RF HOP (<20 ms) ═════════════════════════════════════
    │
====================================================================================================
                                      RECEIVER PHONE (LISTENER)
====================================================================================================
    │
    ▼
 [Step 9: P2P Socket Receiver Daemon]
    │   • Receives 38-byte binary packet; verifies CRC16 checksum.
    ▼
 [Step 10: Protobuf Unpacker & Translation Engine (IndicTrans2 INT8)]
    │   • Extracts text, sender callsign, and 16-byte prosody vector.
    │   • Translates text from Hindi to Listener's preferred language (e.g., Tamil: "பிரிவு 4 இல் உதவி அனுப்பவும்").
    ▼
 [Step 11: Local Database Sync & UI Telemetry Update]
    │   • Inserts received packet into local SQLite MessageAuditLog.
    │   • Updates Jetpack Compose UI (displays text transcript + 38-byte telemetry).
    ▼
 [Step 12: On-Device Indic FastPitch + HiFi-GAN TTS Engine]
    │   • Ingests translated text + conditions on the 16-byte prosody vector.
    │   • Synthesizes audio in the original speaker's pitch and urgency in <140ms.
    ▼
 [Step 13: Hardware Priority Audio Playback (STREAM_ALARM)]
        • For SOS alerts: Bypasses Android Mute / Do Not Disturb at 100% volume.
        • Speaks aloud into the receiver's ear!
```

---

## 🗄️ Local Database Architecture (Offline Embedded SQLite / Room)

Because this system operates in **100% offline, zero-infrastructure tactical and disaster zones**, every device acts as an **autonomous edge database node** powered by **Android Room / SQLite**:

```
+----------------------------------------------------------------------------------------------------+
|                                    EMBEDDED LOCAL DATABASE (ROOM / SQLITE)                         |
+----------------------------------------------------------------------------------------------------+

  [ Table 1: MessageAuditLog ]          [ Table 2: MeshPeerRegistry ]        [ Table 3: EmergencyCodebook ]
  - message_id (UUID Primary Key)       - node_callsign (Primary Key)        - code_id (e.g. 0x01)
  - timestamp_epoch_ms                  - mac_address / p2p_ip               - short_macro (e.g. "SOS_FIRE")
  - sender_callsign                     - transport_type (WiFi_Direct/BT)    - expanded_text_hi (Hindi)
  - receiver_callsign                   - last_seen_timestamp                - expanded_text_ta (Tamil)
  - priority_level (0, 1, 2)            - link_quality_rssi (dBm)            - priority (CRITICAL)
  - original_transcript                 - battery_level_pct
  - translated_transcript               - hop_count (1, 2, 3...)
  - source_language ("hi")
  - target_language ("ta")
  - payload_size_bytes (e.g., 38)
  - airtime_latency_ms (e.g., 18)
  - delivery_status (SENT/ACKED/FAILED)
```

---

## 👥 Exhaustive 6-Member Work Distribution & Toolchains

```
                                  6-MEMBER COLLABORATION TOPOLOGY
                                  -------------------------------
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 1] Audio Ingestion, Silero VAD Gatekeeper & IndicConformer STT Engine            |
  +--------------------------------------------+--------------------------------------------+
                                               | (Decoded Transcript + Confidence + Lang ID)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 3] Semantic Compression, Indic Translation Bridge & Binary Protobuf Framer       |
  +--------------------------------------------+--------------------------------------------+
                                               | (Framed 40-Byte Binary Payload + CRC16)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 4] P2P Wireless Transport Layer (Wi-Fi Direct, Bluetooth RFCOMM & BLE Mesh)      |
  +--------------------------------------------+--------------------------------------------+
                                               | (Wireless Hop across Phones)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 2] On-Device Indic TTS Engine, Voice Tone Cloner & STREAM_ALARM Playback        |
  +-----------------------------------------------------------------------------------------+
                                               ^
                                               | (JNI Data Binding & State Events)
  +--------------------------------------------+--------------------------------------------+
  | [MEMBER 5] Native Android Core, PTT State Machine, Foreground Daemon & JNI Glue          |
  +-----------------------------------------------------------------------------------------+
                                               ^
                                               | (Reactive StateFlow & Telemetry Pipes)
  +--------------------------------------------+--------------------------------------------+
  | [MEMBER 6] Tactical UI/UX, Telemetry Dashboard, Battery Profiler & Live Demo Harness    |
  +-----------------------------------------------------------------------------------------+
```

---

### 👤 Member 1: Audio Ingestion, Silero VAD & On-Device Indic STT Lead
* **Domain:** AI Speech Recognition, Digital Signal Processing (DSP) & Edge Acceleration
* **Mission:** Ingest low-latency raw microphone audio, execute micro-VAD speech gating to keep idle CPU $<3\%$, and run INT8 quantized Indic speech recognition offline.

#### Exact Tools, Libraries & Compilers:
* **AI/ML & Quantization:** PyTorch 2.2+, ONNX 1.16+, ONNX Runtime Mobile C++ API v1.17+, `onnxruntime-extensions`.
* **Audio & DSP:** Google Oboe C++ Library (v1.8+), AAudio / OpenSL ES native backend, Librosa, SoundFile.
* **Build Systems & Toolchains:** Android NDK r26c, CMake 3.22+, Clang C++20, Python 3.10+.
* **Models:** Silero VAD v5 ONNX (~1.8 MB), AI4Bharat `IndicConformer` / `IndicWav2Vec` (INT8 Quantized, ~35 MB).

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/audio/OboeAudioRecorder.cpp` & `AudioRingBuffer.hpp`:**
   * Build a non-blocking audio capture engine (16 kHz, 16-bit Mono PCM).
   * Implement a lock-free circular ring buffer processing 30 ms chunks (480 samples) with zero dynamic runtime allocation.
2. **`app/src/main/cpp/ml/SileroVAD.cpp`:**
   * Run Silero VAD ONNX model with an inference budget $<1	ext{ ms}$ per frame.
   * Enforce thresholding: Speech onset requires 3 consecutive positive frames (>0.55 probability); speech offset requires 600ms silence (<0.35 probability).
3. **`models_training/export_stt_onnx.py` & `app/src/main/cpp/ml/IndicSTTEngine.cpp`:**
   * Export AI4Bharat IndicConformer to ONNX with dynamic sequence length.
   * Apply Static INT8 Post-Training Quantization using calibration clips from the *Kathbath* dataset.
   * Build C++ inference wrapper using XNNPACK execution provider and CTC greedy decoding.
4. **Model Asset Deliverables:**
   * `app/src/main/assets/models/silero_vad.onnx` (~1.8 MB)
   * `app/src/main/assets/models/indic_stt_int8.onnx` (~35.0 MB)

#### Interface Contract & Handoff:
* **Input:** Raw microphone stream.
* **Output:** `struct STTResult { std::string transcript; std::string lang_code; float confidence; uint32_t duration_ms; }`
* **Handoff:** Passes `STTResult` directly to **Member 3** for arithmetic tokenization.

---

### 👤 Member 2: On-Device Indic TTS, Voice Tone Cloner & Audio Playback Lead
* **Domain:** Neural Acoustic Modeling, Speech Synthesis & Android Audio Framework
* **Mission:** Reconstruct natural Indic speech from text packets, inject speaker pitch/emotion via a 16-byte vector, and enforce non-interruptible `STREAM_ALARM` playback.

#### Exact Tools, Libraries & Compilers:
* **AI/ML & Quantization:** PyTorch, FastPitch Acoustic Model, HiFi-GAN Vocoder, MB-MelGAN, ONNX Runtime Mobile C++ API.
* **Android Audio:** Android `AudioManager`, `AudioTrack`, `AudioAttributes`, Google Oboe Audio Player.
* **Build Systems:** Android NDK r26c, CMake 3.22+, Clang C++20.
* **Models:** AI4Bharat `Indic-FastPitch` INT8 (~28 MB), `HiFi-GAN` Vocoder INT8 (~14 MB).

#### Detailed Tasks & File Deliverables:
1. **`models_training/export_tts_onnx.py` & `app/src/main/cpp/ml/IndicTTSEngine.cpp`:**
   * Export FastPitch Mel-Spectrogram predictor and HiFi-GAN Vocoder to ONNX INT8.
   * Implement multi-threaded inference executing in $<140	ext{ ms}$ for a 5-second sentence on ARM Cortex-A55.
2. **`app/src/main/cpp/ml/VoiceToneCloner.cpp`:**
   * Condition FastPitch duration and pitch predictors on a 16-byte **Prosody Vector** ($F_0$ pitch contour + $d$-vector timbre + urgency level: Calm, Tactical, SOS).
3. **`app/src/main/cpp/audio/OboeAudioPlayer.cpp`:**
   * Low-latency PCM stream renderer outputting 22,050 Hz 16-bit audio to hardware DAC with zero buffer underruns.
4. **`app/src/main/java/org/isro/itantra/audio/AlarmAudioRouter.kt`:**
   * Route SOS packets to `AudioAttributes.USAGE_ALARM` with `AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE` and `FLAG_AUDIBILITY_ENFORCED`, forcing speaker volume to 100% even if the phone is on Silent/DND.
5. **Model Asset Deliverables:**
   * `app/src/main/assets/models/indic_fastpitch_int8.onnx` (~28.0 MB)
   * `app/src/main/assets/models/hifigan_vocoder_int8.onnx` (~14.0 MB)

#### Interface Contract & Handoff:
* **Input:** `struct PacketPayload { std::string text; std::string target_lang; uint8_t prosody[16]; uint8_t priority; }`
* **Output:** Audible speech output + playback completion event dispatched to **Member 5**.

---

### 👤 Member 3: Semantic Compression, Translation Bridge & Serialization Lead
* **Domain:** NLP Tokenization, Machine Translation, Information Theory & Cryptography
* **Mission:** Compress text transcripts to $<30	ext{ bytes}$, translate across Indian dialects offline, and package binary frames with CRC16/FEC error correction.

#### Exact Tools, Libraries & Compilers:
* **Serialization & NLP:** Google Protocol Buffers (Protobuf Lite 3.25+), Python `sentencepiece`, `IndicTrans2-Distilled-INT8`.
* **Cryptography & Math:** Libsodium / Crypto++ (AES-128-GCM), CRC16-CCITT implementation, Reed-Solomon (255, 223) FEC.
* **Build Systems:** CMake 3.22+, Clang C++20, Protoc Compiler.

#### Detailed Tasks & File Deliverables:
1. **`proto/packet_schema.proto`:**
   * Define compact Protobuf Lite schema with 10-byte fixed header: Magic Byte (`0x41475931`), Seq Num, Epoch Timestamp, Priority Flag, Callsign, Lang Code, Compressed Payload, Prosody Vector, CRC16.
2. **`app/src/main/cpp/protocol/ArithmeticTokenizer.cpp`:**
   * Implement custom Indic sub-word byte-pair tokenizer with arithmetic entropy coding (compresses text by 75% vs. raw UTF-8).
3. **`app/src/main/cpp/ml/IndicTranslationEngine.cpp`:**
   * Deploy distilled `IndicTrans2-INT8` (~24 MB) for offline dialect-to-dialect translation (e.g., Tamil $\leftrightarrow$ Hindi in $<80	ext{ ms}$).
4. **`app/src/main/cpp/protocol/PacketFramer.cpp` & `CRC16.cpp`:**
   * Assemble and validate binary frames; compute CRC16 and apply Reed-Solomon FEC for high-BER RF links.
5. **Model Asset Deliverables:**
   * `app/src/main/assets/models/indic_trans_int8.onnx` (~24.0 MB)

#### Interface Contract & Handoff:
* **TX Path:** Input: `STTResult` $ightarrow$ Output: `std::vector<uint8_t> binary_packet` (35–45 bytes).
* **RX Path:** Input: `raw_bytes` $ightarrow$ Output: `DecodedVoiceMessage` (Translated text + prosody vector).
* **Handoff:** Passes binary packet to **Member 4** for transmission, and passes decoded message to **Member 2** for synthesis.

---

### 👤 Member 4: P2P Wireless Transport & Mesh Networking Lead
* **Domain:** Wireless Telecommunications, RF Protocol Engineering & Networking
* **Mission:** Establish 100% offline, resilient peer-to-peer radio links using Wi-Fi Direct, Bluetooth RFCOMM, and store-and-forward mesh relay.

#### Exact Tools, Libraries & Compilers:
* **Wireless Frameworks:** Android Wi-Fi P2P (`WifiP2pManager`), Bluetooth Classic (`BluetoothServerSocket`, `BluetoothSocket`), BLE L2CAP, Java NIO non-blocking socket channels.
* **Network Diagnostics:** Wireshark, Android Network Service Discovery (NSD / mDNS), RF Signal Profiler.
* **Build Systems:** Android SDK (API 30+), Kotlin Coroutines & Flow.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/java/org/isro/itantra/network/WifiP2pTransport.kt`:**
   * Autonomous peer discovery, service advertisement (DNS-SD), and Group Owner (GO) negotiation.
   * Persistent non-blocking TCP socket server on port `8988`.
2. **`app/src/main/java/org/isro/itantra/network/BluetoothTransport.kt`:**
   * Parallel Bluetooth Classic RFCOMM server and BLE L2CAP socket listener.
3. **`app/src/main/java/org/isro/itantra/network/P2PTransportManager.kt`:**
   * **Dual-Mode Autonomous Failover:** If Wi-Fi Direct RSSI drops below $-85	ext{ dBm}$ or packet loss exceeds 20%, seamlessly switch packet dispatch to Bluetooth in $<50	ext{ ms}$.
4. **`app/src/main/java/org/isro/itantra/network/MeshRelayRouter.kt` & `SelectiveAckQueue.kt`:**
   * Multi-hop epidemic flooding relay with 64-entry LRU packet-ID deduplication and selective ACK retransmissions.

#### Interface Contract & Handoff:
* **Send API:** `fun sendPacket(bytes: ByteArray, targetCallsign: String?, priority: PriorityLevel)`
* **Receive Flow:** `val onPacketReceivedFlow: SharedFlow<ByteArray>`
* **Handoff:** Transmits byte stream from **Member 3**; bound to service lifecycle by **Member 5**.

---

### 👤 Member 5: Native Android Core, State Machine & Database Systems Lead
* **Domain:** Android Native Architecture (NDK/JNI), Lifecycle Management & Edge Databases
* **Mission:** Build the master Android application architecture, manage the multi-threaded JNI bridge, run the 24/7 background radio daemon, and manage local SQLite storage.

#### Exact Tools, Libraries & Compilers:
* **Frameworks & Storage:** Android Architecture Components (Coroutines, StateFlow, ViewModel), Room Persistence Library (SQLite 3.40+), Android Foreground Services, WakeLock API.
* **Native Integration:** Android NDK r26c, CMake 3.22+, JNI (Java Native Interface), `DirectByteBuffer`.
* **Build Systems:** Android Studio Hedgehog/Iguana, Gradle 8.4+, Kotlin 1.9+.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/native_bridge.cpp`:**
   * High-performance JNI bindings connecting Kotlin to native C++ engines with zero memory copies using `DirectByteBuffer`.
2. **`app/src/main/java/org/isro/itantra/domain/PTTStateMachine.kt`:**
   * Deterministic state engine: `IDLE_LISTENING` $\leftrightarrow$ `PTT_CAPTURING` $\leftrightarrow$ `TRANSMITTING` $\leftrightarrow$ `RECEIVING` $\leftrightarrow$ `ALARM_ACTIVE`.
   * Hardware volume button interceptor (`KEYCODE_VOLUME_DOWN`) to toggle PTT even when screen is locked.
3. **`app/src/main/java/org/isro/itantra/service/RadioDaemonService.kt`:**
   * Background Foreground Service with `START_STICKY`, persistent notification, and `PARTIAL_WAKE_LOCK` to keep radio listening active 24/7.
4. **`app/src/main/java/org/isro/itantra/data/local/MessageDatabase.kt` & `MessageDao.kt`:**
   * Room Database implementation for `MessageAuditLog`, `MeshPeerRegistry`, and `EmergencyCodebook`.

#### Interface Contract & Handoff:
* **Exposes:** `val pttStateFlow: StateFlow<PTTState>` and `val messageLogFlow: Flow<List<MessageEntity>>`.
* **Handoff:** Supplies reactive state streams to **Member 6** for UI rendering.

---

### 👤 Member 6: Tactical UI/UX, Live Telemetry Dashboard & QA/Pitch Lead
* **Domain:** Modern Declarative UI, System Benchmarking, Quality Assurance & Hackathon Presentation
* **Mission:** Build the military-grade tactical UI, visual live telemetry monitor, energy profiling harness, and execute the 3-minute winning hackathon live pitch.

#### Exact Tools, Libraries & Compilers:
* **UI & Graphics:** Jetpack Compose, Material Design 3, Canvas 2D Graphics, Compose Animation.
* **Benchmarking & Profiling:** Android Studio Profiler (Energy, CPU, Memory), Android Battery Historian, Simpleperf, `top` CLI.
* **Testing & Design:** JUnit 5, Espresso, MockK, Figma, Markdown.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/java/org/isro/itantra/ui/screens/MainWalkieTalkieScreen.kt`:**
   * High-contrast tactical dark-theme interface (`#0B0E14` background with `#00E5FF` and `#FF3D00` tactical accents).
2. **`app/src/main/java/org/isro/itantra/ui/components/TacticalPTTButton.kt` & `AudioWaveformVisualizer.kt`:**
   * Central haptic PTT button with active state animations and dynamic audio FFT waveform visualizer.
3. **`app/src/main/java/org/isro/itantra/ui/components/LiveTelemetryOverlay.kt`:**
   * Real-time hardware telemetry display: `Payload Size (38 Bytes)`, `Airtime Latency (18 ms)`, `Data Saved (99.8%)`, `Carrier (Wi-Fi Direct / BT)`.
4. **`app/src/main/java/org/isro/itantra/ui/components/DemoInjectionDrawer.kt`:**
   * Test harness with one-touch triggers: `[Simulate Airplane Mode]`, `[Inject 40% Packet Loss]`, `[Trigger SOS Max Volume Alarm]`, `[Toggle Hindi -> Tamil]`.
5. **`docs/benchmarks/Energy_CPU_Benchmark_Report.pdf`:**
   * Profile and document $<3\%$ idle CPU load to secure full marks on the 20% evaluation rubric.

#### Interface Contract & Handoff:
* **Handoff:** Owns final APK packaging, multi-device field testing, and live presentation defense.

---

## 🛠️ Complete Technology Stack

| Layer | Technology | Purpose & Rationale |
| :--- | :--- | :--- |
| **Operating Platform** | Android 11+ (API 30+) | Universal deployment on budget ₹8,000–₹15,000 phones. |
| **Mobile UI** | Kotlin + Jetpack Compose | Modern declarative UI; state-driven reactivity. |
| **Native Performance Core** | C++20 via Android NDK (JNI) | Zero-overhead DSP, lock-free ring buffers, SIMD math. |
| **Audio Pipeline** | Google Oboe (AAudio/OpenSL) | Sub-10ms low-latency audio capture and rendering. |
| **Voice Activity Detector** | Silero VAD v5 (ONNX Mobile) | 1.8 MB model; <1ms inference per 30ms window; <3% idle CPU. |
| **On-Device STT** | AI4Bharat IndicConformer (INT8) | High-accuracy Indic phonetics; compressed to ~35 MB. |
| **On-Device TTS** | FastPitch + HiFi-GAN Vocoder (INT8)| Natural neural speech synthesis in <150ms on mobile CPU. |
| **Offline Translation (NMT)**| IndicTrans2-Distilled (INT8) | On-device dialect translation without cloud APIs (<25 MB). |
| **Inference Engine** | ONNX Runtime Mobile v1.17+ | Optimized for ARM XNNPACK and NNAPI acceleration. |
| **Wireless Transport** | Wi-Fi Direct (`WifiP2pManager`) + BT | Autonomous peer discovery, group owner election, 50m–100m range. |
| **Serialization** | Protocol Buffers (Protobuf Lite) | Compact structured binary schema with CRC16 error detection. |
| **Local Audit Database** | SQLite via Room Library | Offline chronological indexing of all received/sent voice packets. |

---

## 📦 Binary Packet Specification (`packet_schema.proto`)

```protobuf
syntax = "proto3";
package itantra.protocol;

enum PriorityLevel {
  ROUTINE = 0;
  TACTICAL = 1;
  LIFE_SAFETY_ALERT = 2;
}

message VoicePacket {
  uint32 magic_header = 1;       // 0x41475931 (AGY1)
  uint32 sequence_number = 2;   // Rolling packet counter
  uint64 timestamp_ms = 3;       // Sender epoch time
  PriorityLevel priority = 4;    // Priority routing (0, 1, 2)
  string source_callsign = 5;    // e.g., "RESCUE_LEADER_01"
  string source_language = 6;    // ISO 639-1 code (e.g., "hi", "ta", "mr")
  
  bytes compressed_payload = 7;  // Phoneme / Tokenized semantic text (15-30B)
  bytes prosody_vector = 8;      // 16-byte pitch & speaker identity vector
  uint32 crc16_checksum = 9;     // Error detection checksum
}
```

---

## 📅 10-Day Sprint Plan

```
+----------------------------------------------------------------------------------------------------+
|                                    10-DAY SPRINT SCHEDULE                                          |
+----------------------------------------------------------------------------------------------------+

 Day 1 - 2: Foundation & Interfaces
 ├── M1: Export Silero VAD & IndicConformer to ONNX; test desktop inference.
 ├── M2: Export Indic FastPitch + HiFi-GAN to ONNX; verify speech synthesis.
 ├── M3: Define `packet_schema.proto`; generate C++ and Kotlin bindings.
 ├── M4: Build standalone Android Wi-Fi Direct discovery sample app.
 ├── M5: Scaffold Android Studio monorepo with CMake NDK bridge and JNI stubs.
 └── M6: Design high-contrast Figma UI assets and build Jetpack Compose theme.

 Day 3 - 5: Core Engineering & Quantization
 ├── M1: Quantize STT model to INT8 (<38MB); integrate Oboe audio capture.
 ├── M2: Quantize TTS model to INT8 (<45MB); implement `STREAM_ALARM` audio track.
 ├── M3: Build IndicTrans2 translation bridge and arithmetic tokenizer.
 ├── M4: Complete non-blocking async socket server; add Bluetooth fallback.
 ├── M5: Build PTT state machine and foreground service lifecycle handlers.
 └── M6: Implement real-time waveform visualizer and P2P peer radar screen.

 Day 6 - 7: Native Integration & JNI Fusion
 ├── Merge M1 (STT) + M2 (TTS) + M3 (Protocol) into native shared library (`.so`).
 ├── Connect M4 (P2P Transport) to M5 (Foreground Service).
 ├── Connect M5 (JNI Engine) to M6 (Compose UI StateFlows).
 └── First full-loop on single phone: Speak -> VAD -> STT -> Packet -> TTS -> Speaker.

 Day 8 - 9: End-to-End P2P Testing & Battery Profiling
 ├── Two-device P2P field testing across physical distance (10m, 30m, 60m).
 ├── Test cross-lingual translation: Hindi speech -> Tamil synthesis.
 ├── Test Emergency Priority: Verify DND override at 100% volume.
 └── Profile with Android Battery Historian to confirm <3% idle CPU load.

 Day 10: Freeze, Polish & Live Demo Setup
 ├── Compile signed release APKs and install on 2 target demonstration phones.
 ├── Prepare Airplane Mode demo harness with real-time telemetry metrics.
 └── Dry run the 3-minute pitch sequence with simulated radio channel noise.
```

---

## 🎤 3-Minute Live Hackathon Demo Script

1. **Act 1: Airplane Mode Setup (20s):** Place both phones in complete Airplane Mode (zero internet, zero SIM, zero cloud).
2. **Act 2: Instant Voice Relay (40s):** Speak into Phone A in Hindi (*"सेक्टर 4 में तुरंत सहायता भेजो!"*). Phone B across the room receives the 38-byte packet in <300ms and speaks aloud in natural voice.
3. **Act 3: Emergency Mute Override (40s):** Put Phone B on Silent/DND. Send an SOS Alert → Phone B overrides mute and sounds the alert at 100% volume via `STREAM_ALARM`.
4. **Act 4: 20% Evaluation Metric Proof (30s):** Point to the real-time CPU monitor showing <2.8% CPU load during idle listening, proving all-day field battery life.
