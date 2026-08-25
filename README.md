# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Sponsoring Agency: Indian Space Research Organisation (ISRO)

> **Offline, Edge-Deployable, Multilingual Semantic Walkie-Talkie for Tactical, Disaster, and Ultra-Low-Bitrate Space/Radio Communications.**

---

## 👥 Team Roster & Role Assignment Table

| Member | Assigned Name | Primary Role | Domain & Core Module | Key Tools & Technologies | Major Deliverable Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Member 1** | **Chhavi** | AI Speech Recognition (STT) & DSP Lead | Audio Ingestion, Silero VAD & IndicConformer STT | PyTorch, Google Oboe, ONNX Runtime Mobile, C++20, NDK | `libaudio_stt_core.so`, `indic_stt_int8.onnx`, `silero_vad.onnx` |
| **Member 2** | **Vaibhav Senior** | Neural Speech Synthesis (TTS) & Audio Lead | Edge Indic TTS, Voice Tone Cloner & Audio Playback | FastPitch, HiFi-GAN, Android `STREAM_ALARM`, Oboe, C++ | `libaudio_tts_core.so`, `indic_fastpitch_int8.onnx`, `AlarmAudioRouter.kt` |
| **Member 3** | **Parth Karpe** | Semantic Compression & NLP Lead | Tokenization, Indic Translation Bridge & Protobuf Framer | Protocol Buffers (Lite), `IndicTrans2`, AES-128-GCM, CRC16 | `packet_schema.proto`, `libsemantic_protocol.so`, `indic_trans_int8.onnx` |
| **Member 4** | **M Janaki** | P2P Wireless Transport & WFB-ng Protocol Lead | WFB-ng Resilient UDP + FEC, Wi-Fi Direct, Bluetooth & Mesh | Android `WifiP2pManager`, Libsodium ChaCha20, Reed-Solomon FEC, Java NIO | `WfbngTransportManager.kt`, `ReedSolomonFEC.kt`, `WifiP2pTransport.kt` |
| **Member 5** | **Nupur** | Native Android Core & Database Lead | PTT State Machine, Foreground Daemon & JNI Bridge | Kotlin, JNI, CMake, Room (SQLite), Android Foreground Service | `native_bridge.cpp`, `RadioDaemonService.kt`, `MessageDatabase.kt` |
| **Member 6** | **Vaibhav Junior** | Tactical UI/UX & Benchmark/Pitch Lead | Jetpack Compose UI, Telemetry Overlay & QA Harness | Jetpack Compose, Material 3, Android Studio Profiler | `MainWalkieTalkieScreen.kt`, `LiveTelemetryOverlay.kt`, Benchmark Report |

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

 [Step 1: User Presses PTT / Speaks] (Member 5: Nupur & Member 6: Vaibhav Junior)
    │
    ▼
 [Step 2: Google Oboe Audio Capture (C++ NDK)] (Member 1: Chhavi)
    │   • Captures raw 16kHz 16-bit Mono PCM audio in 30ms lock-free chunks (480 samples).
    ▼
 [Step 3: Silero VAD Gatekeeper (<1ms)] (Member 1: Chhavi)
    │   • Detects human voice onset and cutoff.
    │   • Gates subsequent heavy AI models so they sleep during silence (<3% idle CPU).
    ▼
 [Step 4: AI4Bharat IndicConformer STT Engine (INT8 ONNX)] (Member 1: Chhavi)
    │   • Processes the captured speech audio segment.
    │   • Outputs raw text transcript: "सेक्टर 4 में तुरंत मदद भेजो" + Language ID ("hi").
    ▼
 [Step 5: Prosody & Voice Feature Extractor] (Member 2: Vaibhav Senior)
    │   • Extracts 16-byte vector containing pitch contour (F0) + speaker timbre + urgency flag.
    ▼
 [Step 6: Arithmetic Tokenizer & Protobuf Framer] (Member 3: Parth Karpe)
    │   • Compresses UTF-8 text down to 22 bytes.
    │   • Packages binary frame: [Header | Priority: SOS | Lang: HI | Prosody | Payload | CRC16].
    │   • Total packet size: 38 Bytes!
    ▼
 [Step 7: Local Database Insertion (Room / SQLite)] (Member 5: Nupur)
    │   • Logs message in local SQLite database with status "TRANSMITTING".
    ▼
 [Step 8: WFB-ng FEC Encoder & Radio Transmitter] (Member 4: M Janaki)
    │   • Generates Reed-Solomon FEC Parity Blocks (survives 40% RF packet loss).
    │   • Encrypts via Libsodium ChaCha20-Poly1305.
    │   • Transmits over Connectionless UDP Wi-Fi Direct / BT RFCOMM.
    │
═════════════════════════════════════ WIRELESS RF HOP (<20 ms) ═════════════════════════════════════
    │
====================================================================================================
                                      RECEIVER PHONE (LISTENER)
====================================================================================================
    │
    ▼
 [Step 9: WFB-ng Receiver Daemon & FEC Decoder] (Member 4: M Janaki)
    │   • Ingests UDP datagrams; decrypts with Libsodium.
    │   • Recovers corrupted/dropped packets via Reed-Solomon FEC without retransmission delay.
    ▼
 [Step 10: Protobuf Unpacker & Translation Engine (IndicTrans2 INT8)] (Member 3: Parth Karpe)
    │   • Extracts text, sender callsign, and 16-byte prosody vector.
    │   • Translates text from Hindi to Listener's preferred language (e.g., Tamil: "பிரிவு 4 இல் உதவி அனுப்பவும்").
    ▼
 [Step 11: Local Database Sync & UI Telemetry Update] (Member 5: Nupur & Member 6: Vaibhav Junior)
    │   • Inserts received packet into local SQLite MessageAuditLog.
    │   • Updates Jetpack Compose UI (displays text transcript + 38-byte telemetry).
    ▼
 [Step 12: On-Device Indic FastPitch + HiFi-GAN TTS Engine] (Member 2: Vaibhav Senior)
    │   • Ingests translated text + conditions on the 16-byte prosody vector.
    │   • Synthesizes audio in the original speaker's pitch and urgency in <140ms.
    ▼
 [Step 13: Hardware Priority Audio Playback (STREAM_ALARM)] (Member 2: Vaibhav Senior)
        • For SOS alerts: Bypasses Android Mute / Do Not Disturb at 100% volume.
        • Speaks aloud into the receiver's ear!
```

---

## 🗄️ Local Database Architecture (Offline Embedded SQLite / Room)

Because this system operates in **100% offline, zero-infrastructure tactical and disaster zones**, every device acts as an **autonomous edge database node** powered by **Android Room / SQLite** (Managed by **Member 5: Nupur**):

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

## ⚡ 4 Operational State Machine Flows

```
+----------------------------------------------------------------------------------------------------+
|                                      SYSTEM STATE MACHINE FLOW                                     |
+----------------------------------------------------------------------------------------------------+

 1. IDLE LISTENING STATE (Battery-Saver Mode):
    [Mic Ingestion (Oboe)] ---> [Silero VAD (<1ms)] ---> (Is Speech Detected?)
                                                               │
                                     +-------------------------+-------------------------+
                                     | No                                                | Yes
                                     v                                                   v
                          [Remain in Sleep Mode]                              [Wake STT Model]
                          (CPU < 2.8%, Zero Battery Drain)                    (Start Audio Capture)

 2. TRANSMISSION STATE (PTT Pressed):
    [Voice Spoken] -> [STT Transcription] -> [Tokenize (38B)] -> [SQLite DB Save] -> [WFB-ng FEC TX]

 3. RECEPTION STATE (Background Daemon):
    [WFB-ng UDP Rx] -> [FEC Reconstruction] -> [NMT Translate] -> [SQLite DB Save] -> [TTS Synthesize] -> [Speaker]

 4. EMERGENCY OVERRIDE STATE (SOS Priority):
    [Priority == 2] -> [Request AudioManager.STREAM_ALARM] -> [Force Max Volume] -> [Play Non-Duckable]
```

---

## 👥 6-Member Balanced Work Breakdown

---

### 👤 Member 4 (M Janaki): Updated WFB-ng Responsibilities & Deliverables

* **Domain:** Wireless Telecommunications, RF Protocol Engineering & Resilient P2P Networking
* **Mission:** Build a 100% offline, battle-tested radio transport stack adopting the WFB-ng (Wi-Fi Broadcast Next Generation) protocol paradigm with Forward Error Correction (FEC), connectionless UDP datagrams, Libsodium authenticated encryption, and autonomous Bluetooth fallback.

#### Exact Tools & Compilers for Janaki:
* **Protocol & Wireless:** WFB-ng Architecture, Android Wi-Fi P2P (`WifiP2pManager`), Android Wi-Fi Aware (NAN), Bluetooth Classic RFCOMM (`BluetoothServerSocket`), BLE L2CAP.
* **FEC & Cryptography:** Reed-Solomon / Cauchy Block Forward Error Correction (FEC), Libsodium (`crypto_aead_chacha20poly1305`), Java NIO Non-Blocking Datagram Channels (`DatagramChannel`).
* **Diagnostics & Toolchains:** Wireshark, Android SDK (API 30+), Kotlin Coroutines & Flow, Linux `libpcap` (for C++ Edge Engine).

#### Exact Code Files Janaki Will Write:
1. **`app/src/main/java/org/isro/itantra/network/ReedSolomonFEC.kt`:**
   * Block Forward Error Correction: Generates $M$ parity blocks for $K$ data packets ($8$ data $+ 4$ parity).
   * Recovers dropped or corrupted speech packets with **zero retransmission delay**, surviving up to **40% RF packet loss**.
2. **`app/src/main/java/org/isro/itantra/network/WifiP2pTransport.kt`:**
   * Autonomous peer discovery and Group Owner (GO) negotiation.
   * High-throughput, non-blocking UDP Datagram socket server on port `8988` (eliminates TCP head-of-line blocking).
3. **`app/src/main/java/org/isro/itantra/network/BluetoothTransport.kt`:**
   * Parallel Bluetooth Classic RFCOMM server and BLE L2CAP listener for short-range/low-power failover.
4. **`app/src/main/java/org/isro/itantra/network/WfbngTransportManager.kt`:**
   * Master Transceiver Controller: Encrypts outgoing payloads with Libsodium ChaCha20-Poly1305, attaches FEC parity frames, and manages autonomous link failover to Bluetooth in $<50	ext{ ms}$.
5. **`app/src/main/java/org/isro/itantra/network/MeshRelayRouter.kt`:**
   * Multi-hop store-and-forward relay with a 64-entry LRU ring of packet hashes to prevent routing loops.
6. **`edge_engine/wfbng_raw_injector.cpp` (For C++ Linux/SDR Edge Deliverable):**
   * Standalone C++ module implementing raw IEEE 802.11 monitor mode packet injection via `libpcap` for external Raspberry Pi / Linux tactical nodes with RTL8812AU Wi-Fi adapters.

---

### 👤 Member 1 (Chhavi): Audio Ingestion, Silero VAD & On-Device Indic STT Lead
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

---

### 👤 Member 2 (Vaibhav Senior): On-Device Indic TTS, Voice Tone Cloner & Audio Playback Lead
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

---

### 👤 Member 3 (Parth Karpe): Semantic Compression, Translation Bridge & Serialization Lead
* **Domain:** NLP Tokenization, Machine Translation, Information Theory & Cryptography
* **Mission:** Compress text transcripts to $<30	ext{ bytes}$, translate across Indian dialects offline, and package binary frames with CRC16/FEC error correction.

#### Exact Tools, Libraries & Compilers:
* **Serialization & NLP:** Google Protocol Buffers (Protobuf Lite 3.25+), Python `sentencepiece`, `IndicTrans2-Distilled-INT8`.
* **Cryptography & Math:** Libsodium / Crypto++ (AES-128-GCM), CRC16-CCITT implementation.
* **Build Systems:** CMake 3.22+, Clang C++20, Protoc Compiler.

#### Detailed Tasks & File Deliverables:
1. **`proto/packet_schema.proto`:**
   * Define compact Protobuf Lite schema with 10-byte fixed header: Magic Byte (`0x41475931`), Seq Num, Epoch Timestamp, Priority Flag, Callsign, Lang Code, Compressed Payload, Prosody Vector, CRC16.
2. **`app/src/main/cpp/protocol/ArithmeticTokenizer.cpp`:**
   * Implement custom Indic sub-word byte-pair tokenizer with arithmetic entropy coding (compresses text by 75% vs. raw UTF-8).
3. **`app/src/main/cpp/ml/IndicTranslationEngine.cpp`:**
   * Deploy distilled `IndicTrans2-INT8` (~24 MB) for offline dialect-to-dialect translation (e.g., Tamil $\leftrightarrow$ Hindi in $<80	ext{ ms}$).
4. **`app/src/main/cpp/protocol/PacketFramer.cpp` & `CRC16.cpp`:**
   * Assemble and validate binary frames; compute CRC16 for transmission integrity.
5. **Model Asset Deliverables:**
   * `app/src/main/assets/models/indic_trans_int8.onnx` (~24.0 MB)

---

### 👤 Member 5 (Nupur): Native Android Core, State Machine & Database Systems Lead
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

---

### 👤 Member 6 (Vaibhav Junior): Tactical UI/UX, Live Telemetry Dashboard & QA/Pitch Lead
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
   * Real-time hardware telemetry display: `Payload Size (38 Bytes)`, `Airtime Latency (18 ms)`, `Data Saved (99.8%)`, `WFB-ng FEC Parity (4 Blocks)`, `Carrier (Wi-Fi Direct / BT)`.
4. **`app/src/main/java/org/isro/itantra/ui/components/DemoInjectionDrawer.kt`:**
   * Test harness with one-touch triggers: `[Simulate Airplane Mode]`, `[Inject 40% Packet Loss]`, `[Trigger SOS Max Volume Alarm]`, `[Toggle Hindi -> Tamil]`.
5. **`docs/benchmarks/Energy_CPU_Benchmark_Report.pdf`:**
   * Profile and document $<3\%$ idle CPU load to secure full marks on the 20% evaluation rubric.

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
| **Wireless Transport** | WFB-ng UDP + Reed-Solomon FEC | Connectionless UDP datagrams, Libsodium encryption, 40% loss immunity. |
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
 ├── M1 (Chhavi): Export Silero VAD & IndicConformer to ONNX; test desktop inference.
 ├── M2 (Vaibhav Senior): Export Indic FastPitch + HiFi-GAN to ONNX; verify speech synthesis.
 ├── M3 (Parth Karpe): Define `packet_schema.proto`; generate C++ and Kotlin bindings.
 ├── M4 (M Janaki): Build standalone Android Wi-Fi Direct discovery sample app with UDP sockets.
 ├── M5 (Nupur): Scaffold Android Studio monorepo with CMake NDK bridge and JNI stubs.
 └── M6 (Vaibhav Junior): Design high-contrast Figma UI assets and build Jetpack Compose theme.

 Day 3 - 5: Core Engineering & Quantization
 ├── M1 (Chhavi): Quantize STT model to INT8 (<38MB); integrate Oboe audio capture.
 ├── M2 (Vaibhav Senior): Quantize TTS model to INT8 (<45MB); implement `STREAM_ALARM` audio track.
 ├── M3 (Parth Karpe): Build IndicTrans2 translation bridge and arithmetic tokenizer.
 ├── M4 (M Janaki): Implement Reed-Solomon FEC encoder/decoder + Libsodium ChaCha20 encryption.
 ├── M5 (Nupur): Build PTT state machine and foreground service lifecycle handlers.
 └── M6 (Vaibhav Junior): Implement real-time waveform visualizer and P2P peer radar screen.

 Day 6 - 7: Native Integration & JNI Fusion
 ├── Merge M1 (STT) + M2 (TTS) + M3 (Protocol) into native shared library (`.so`).
 ├── Connect M4 (WFB-ng Transport) to M5 (Foreground Service).
 ├── Connect M5 (JNI Engine) to M6 (Compose UI StateFlows).
 └── First full-loop on single phone: Speak -> VAD -> STT -> Packet -> TTS -> Speaker.

 Day 8 - 9: End-to-End P2P Testing & Battery Profiling
 ├── Two-device P2P field testing across physical distance (10m, 30m, 60m).
 ├── Test cross-lingual translation: Hindi speech -> Tamil synthesis.
 ├── Test Emergency Priority: Verify DND override at 100% volume.
 ├── Inject 40% packet loss to demonstrate WFB-ng Reed-Solomon FEC recovery live!
 └── Profile with Android Battery Historian to confirm <3% idle CPU load.

 Day 10: Freeze, Polish & Live Demo Setup
 ├── Compile signed release APKs and install on 2 target demonstration phones.
 ├── Prepare Airplane Mode demo harness with real-time telemetry metrics.
 └── Dry run the 3-minute pitch sequence with simulated radio channel noise.
```

---

## 🎤 3-Minute Live Hackathon Demo Script

1. **Act 1: Airplane Mode Setup (20s):** Place both phones in complete Airplane Mode (zero internet, zero SIM, zero cloud).
2. **Act 2: Instant Voice Relay & WFB-ng FEC Proof (40s):** Speak into Phone A in Hindi (*"सेक्टर 4 में तुरंत सहायता भेजो!"*). Phone B across the room receives the 38-byte packet in <300ms, recovers through injected radio noise via Reed-Solomon FEC, and speaks aloud in natural voice.
3. **Act 3: Emergency Mute Override (40s):** Put Phone B on Silent/DND. Send an SOS Alert → Phone B overrides mute and sounds the alert at 100% volume via `STREAM_ALARM`.
4. **Act 4: 20% Evaluation Metric Proof (30s):** Point to the real-time CPU monitor showing <2.8% CPU load during idle listening, proving all-day field battery life.
