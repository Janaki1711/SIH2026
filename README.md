# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Sponsoring Agency: Indian Space Research Organisation (ISRO)

> **Offline, Edge-Deployable, Multilingual Semantic Walkie-Talkie for Tactical, Disaster, and Ultra-Low-Bitrate Space/Radio Communications.**

---

## 🎯 Executive Summary & Core Principle

> **"Do not stream heavy raw audio over fragile, degraded wireless links — compress speech by 2,000× into semantic tokens on-device, transmit 40-byte micro-packets across physical distance, and synthesize natural speech locally."**

Standard voice streaming (Opus, PCM, AMR) requires **16 to 128 kbps**, collapsing completely under RF interference, satellite link bottlenecks, and disaster-induced infrastructure blackouts. **iTantra** implements **Semantic Voice Transmission (Voice → Text → RF → Voice)** directly on edge hardware, enabling **100% intelligible two-way communication at <50 bps** with zero cellular network or internet infrastructure.

```
[Phone A: Transmitter]                                           [Phone B: Receiver]
======================                                           ====================
+------------------------------------+                           +------------------------------------+
| 1. Google Oboe Audio Ingestion     |                           | 8. Speaker (STREAM_ALARM Override) |
|    (16kHz 16-bit PCM Mono Chunks)  |                           |    (Non-duckable 100% Volume Gain) |
+-----------------+------------------+                           +-----------------+------------------+
                  |                                                                ^
                  v                                                                | (Raw Audio Waveform)
+------------------------------------+                           +-----------------+------------------+
| 2. Silero VAD Gatekeeper (<1ms)    |                           | 7. On-Device Indic TTS             |
|    (Keeps idle CPU below 3%)       |                           |    (FastPitch + HiFi-GAN INT8 ONNX)|
+-----------------+------------------+                           +-----------------+------------------+
                  | (Voice Confirmed)                                              ^
                  v                                                                | (Text + Prosody Vector)
+------------------------------------+                           +-----------------+------------------+
| 3. On-Device Indic STT             |                           | 6. Packet Unpacker & Router        |
|    (IndicConformer INT8, ~35MB)    |                           |    (Protobuf Deserializer + CRC16) |
+-----------------+------------------+                           +-----------------+------------------+
                  | (Raw Transcript)                                               ^
                  v                                                                |
+------------------------------------+                           +-----------------+------------------+
| 4. Semantic Compression & NMT      |                           | 5. P2P Socket Receiver Daemon      |
|    (16-Byte Vector + IndicTrans2)  |                           |    (Wi-Fi Direct / BT RFCOMM)      |
+-----------------+------------------+                           +-----------------+------------------+
                  |                                                                ^
                  |=========== [40-Byte Binary Packet via RF] =====================|
```

---

## 👥 Exhaustive 6-Member Work Distribution & Architecture

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
* **Mission:** Transform raw hardware microphone input into high-accuracy offline Indic text while keeping idle CPU consumption under 3% using micro-VAD gating.

#### Detailed Responsibilities & Tasks:
1. **Low-Latency Audio Capture Engine:**
   * Build a C++ audio stream client using **Google Oboe** configured for `16000 Hz`, `16-bit Signed Integer PCM`, `ChannelCount = 1 (Mono)`.
   * Implement a lock-free, zero-allocation circular ring buffer (`AudioRingBuffer.hpp`) to process incoming audio in **30 ms frames** (480 samples per frame) without triggering Android Garbage Collection pauses.
2. **Silero VAD Gatekeeper Pipeline:**
   * Integrate the **Silero VAD v5 ONNX model** (~1.8 MB).
   * Process 30 ms frames through ONNX Runtime with an inference budget of $<1	ext{ ms}$.
   * Maintain a stateful speech probability buffer:
     * If speech probability $> 0.55$ for 3 consecutive frames (90 ms) $ightarrow$ Trigger STT Wakeup state.
     * If speech probability $< 0.35$ for $> 600	ext{ ms}$ $ightarrow$ Mark speech stoppage, flush audio buffer, and return to idle sleep.
3. **AI4Bharat IndicConformer Optimization & Quantization:**
   * Download AI4Bharat `IndicConformer` / `IndicWav2Vec` pre-trained PyTorch weights.
   * Export the model to ONNX with dynamic axis configuration for variable-length speech sequences.
   * Apply **Static INT8 Post-Training Quantization (PTQ)** using calibration audio clips from the *Kathbath* dataset, shrinking model size from ~600 MB down to **~35 MB**.
4. **Native C++ Inference Wrapper:**
   * Build `IndicSTTEngine.cpp` using ONNX Runtime Mobile C++ API with `XNNPACK` and `NNAPI` execution providers.
   * Implement non-autoregressive CTC greedy/beam search decoder returning text tokens, timestamp boundaries, and acoustic confidence score.

#### Technical Specifications & Deliverables:
* **Tech Stack:** PyTorch, ONNX, ONNX Runtime Mobile C++, Google Oboe, C++20, Android NDK, Python.
* **Code Deliverables:**
  * `app/src/main/cpp/audio/OboeAudioRecorder.cpp`
  * `app/src/main/cpp/ml/SileroVAD.cpp`
  * `app/src/main/cpp/ml/IndicSTTEngine.cpp`
  * `app/src/main/assets/models/silero_vad.onnx` (~1.8 MB)
  * `app/src/main/assets/models/indic_stt_int8.onnx` (~35 MB)
* **Input / Output Contracts:**
  * **Input:** Raw microphone stream (16 kHz, 16-bit Mono PCM).
  * **Output:** `struct STTResult { std::string transcript; std::string lang_code; float confidence; uint32_t duration_ms; }`
* **Dependencies & Handoff:** Passes `STTResult` directly to **Member 3** for compression and packaging.

---

### 👤 Member 2: On-Device Indic TTS, Voice Tone Cloner & Audio Playback Lead
* **Domain:** Neural Acoustic Modeling, Speech Synthesis & Android Audio Framework
* **Mission:** Reconstruct natural-sounding Indic speech on the receiving phone from compressed text packets, clone the speaker’s pitch/emotion via a 16-byte vector, and enforce maximum-volume alarm playback.

#### Detailed Responsibilities & Tasks:
1. **Indic-FastPitch & HiFi-GAN Vocoder Quantization:**
   * Export AI4Bharat `Indic-FastPitch` (Mel-Spectrogram predictor) and `HiFi-GAN` / `MB-MelGAN` (Vocoder) to ONNX.
   * Perform INT8 quantization on the acoustic model and FP16 operator fusion on the neural vocoder.
   * Optimize synthesis runtime: Target $<150	ext{ ms}$ latency for a 5-second spoken output on an ARM Cortex-A55 mobile CPU.
2. **Zero-Bitrate Voice Identity & Urgency Injection:**
   * Design a 16-byte **Prosody Conditioning Vector**:
     * Bytes 0–7: Fundamental pitch contour ($F_0$ mean and variance).
     * Bytes 8–13: Speaker acoustic timbre vector ($d$-vector projection).
     * Bytes 14–15: Emotional urgency flag (`0x01: Calm`, `0x02: Elevated`, `0x03: Panicked/SOS`).
   * Condition FastPitch duration and pitch predictors on this vector so the synthesized speech reproduces the sender’s personal pitch and emotional state.
3. **Asynchronous Audio Rendering Engine:**
   * Build `OboeAudioPlayer.cpp` streaming synthesized PCM frames to the Android DAC at 22,050 Hz with zero underruns.
4. **Hardware Priority Alert Override (`STREAM_ALARM`):**
   * Implement Java/Kotlin audio focus interceptor:
     * Standard packets $ightarrow$ Play over `AudioAttributes.USAGE_MEDIA` (`STREAM_MUSIC`).
     * Tactical SOS alerts $ightarrow$ Play over `AudioAttributes.USAGE_ALARM` with `AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE` and `FLAG_AUDIBILITY_ENFORCED`, forcing speaker volume to 100% even if the phone is on Mute or Do Not Disturb.

#### Technical Specifications & Deliverables:
* **Tech Stack:** PyTorch, FastPitch, HiFi-GAN, ONNX Runtime Mobile, C++20, Oboe / AAudio, Android AudioManager.
* **Code Deliverables:**
  * `app/src/main/cpp/ml/IndicTTSEngine.cpp`
  * `app/src/main/cpp/audio/OboeAudioPlayer.cpp`
  * `app/src/main/assets/models/indic_fastpitch_int8.onnx` (~28 MB)
  * `app/src/main/assets/models/hifigan_vocoder_int8.onnx` (~14 MB)
  * `app/src/main/java/org/isro/itantra/audio/AlarmAudioRouter.kt`
* **Input / Output Contracts:**
  * **Input:** `struct PacketPayload { std::string text; std::string target_lang; uint8_t prosody[16]; uint8_t priority; }`
  * **Output:** Low-latency hardware speaker playback + audio focus telemetry.
* **Dependencies & Handoff:** Consumes unpacked payloads from **Member 3** & **Member 4**; reports playback state to **Member 5**.

---

### 👤 Member 3: Semantic Compression, Translation Bridge & Serialization Lead
* **Domain:** Natural Language Processing (NLP), Information Theory & Cryptography
* **Mission:** Compress transcript text to the absolute theoretical limit ($<30	ext{ bytes}$), translate between Indian dialects, and frame binary packets with error-correcting codes.

#### Detailed Responsibilities & Tasks:
1. **Phoneme & Sub-Word Arithmetic Tokenizer:**
   * Build a custom Indic sub-word byte-pair tokenizer with arithmetic entropy coding.
   * Reduce UTF-8 text footprint by **75%**: a 10-word sentence is compressed from 80 bytes of UTF-8 down to **18–22 bytes**.
2. **On-Device Indic-to-Indic Translation Bridge:**
   * Distill and quantize `IndicTrans2-Distilled` into an INT8 ONNX model ($<24	ext{ MB}$).
   * Build on-device translation logic: If Sender speaks Tamil (`ta`) and Receiver is set to Hindi (`hi`), translate text tokens in $<80	ext{ ms}$ on-device prior to TTS synthesis.
3. **Protocol Buffer Binary Framing & Checksums:**
   * Define `packet_schema.proto` and compile optimized C++ and Java Lite bindings.
   * Frame binary packets with a 10-byte fixed header:
     `[MagicByte (4B)][SeqNum (2B)][Timestamp (4B)][Priority (1B)][LangID (1B)][PayloadLen (2B)][Payload (NB)][CRC16 (2B)]`.
   * Implement hardware-accelerated **CRC16-CCITT** and **Reed-Solomon (255, 223)** Forward Error Correction (FEC) to recover corrupted packets across noisy RF links.
4. **Lightweight AES-GCM-128 Encryption (Optional Tactical Mode):**
   * Encrypt payload with AES-128-GCM using pre-shared mission keys (PSK), adding only 16 bytes of authentication tag overhead.

#### Technical Specifications & Deliverables:
* **Tech Stack:** Protocol Buffers (Lite), IndicTrans2, ONNX Runtime Mobile, C++20, Python, Libsodium / Crypto++.
* **Code Deliverables:**
  * `proto/packet_schema.proto`
  * `app/src/main/cpp/protocol/PacketFramer.cpp`
  * `app/src/main/cpp/protocol/ArithmeticTokenizer.cpp`
  * `app/src/main/cpp/ml/IndicTranslationEngine.cpp`
  * `app/src/main/assets/models/indic_trans_int8.onnx` (~24 MB)
* **Input / Output Contracts:**
  * **TX Path:** Input: `STTResult` $ightarrow$ Output: `std::vector<uint8_t> binary_packet` (35–45 bytes).
  * **RX Path:** Input: `raw_bytes` $ightarrow$ Output: `DecodedVoiceMessage` (Translated text + prosody vector).
* **Dependencies & Handoff:** Bridges **Member 1** (STT) $ightarrow$ **Member 4** (Network), and **Member 4** (Network) $ightarrow$ **Member 2** (TTS).

---

### 👤 Member 4: P2P Wireless Transport & Mesh Networking Lead
* **Domain:** Wireless Telecommunications, RF Protocol Design & Systems Networking
* **Mission:** Build a 100% offline, resilient peer-to-peer radio transport network supporting Wi-Fi Direct, Bluetooth RFCOMM, and multi-hop relay.

#### Detailed Responsibilities & Tasks:
1. **Wi-Fi Direct P2P Manager Service:**
   * Implement automated peer discovery, service advertisement (DNS-SD), and autonomous Group Owner (GO) election using Android `WifiP2pManager`.
   * Establish a persistent local TCP socket server on port `8988` with non-blocking Java NIO channels.
2. **Dual-Mode Bluetooth RFCOMM & BLE Fallback:**
   * Build a parallel Bluetooth Classic RFCOMM server (`BluetoothServerSocket`) and BLE L2CAP socket listener.
   * Implement **Autonomous Link Health Monitor**: If Wi-Fi Direct RSSI drops below $-85	ext{ dBm}$ or packet loss exceeds 20%, seamlessly failover packet transmission to Bluetooth in $<50	ext{ ms}$.
3. **Reliable UDP Transport with Selective Repeat ACK:**
   * For broadcast and low-latency modes, implement a lightweight UDP protocol with rolling sequence numbers, sliding window flow control, and immediate negative acknowledgment (NACK) retransmissions.
4. **Multi-Hop Store-and-Forward Mesh Engine:**
   * Implement an epidemic flooding mesh algorithm: Each phone maintains a 64-entry LRU ring of `packet_id` hashes to prevent packet loop storms while hopping packets across out-of-range nodes.

#### Technical Specifications & Deliverables:
* **Tech Stack:** Android Wi-Fi P2P (`WifiP2pManager`), Bluetooth Classic (RFCOMM), Bluetooth Low Energy (BLE), Java NIO, C++ POSIX Sockets.
* **Code Deliverables:**
  * `app/src/main/java/org/isro/itantra/network/WifiP2pTransport.kt`
  * `app/src/main/java/org/isro/itantra/network/BluetoothTransport.kt`
  * `app/src/main/java/org/isro/itantra/network/P2PTransportManager.kt`
  * `app/src/main/java/org/isro/itantra/network/MeshRelayRouter.kt`
* **Input / Output Contracts:**
  * **Send:** `sendPacket(bytes: ByteArray, targetCallsign: String?, priority: Priority)`
  * **Receive:** `onPacketReceivedFlow: SharedFlow<ByteArray>`
* **Dependencies & Handoff:** Transmits byte arrays from **Member 3**; integrated into the app lifecycle by **Member 5**.

---

### 👤 Member 5: Native Android Core, State Machine & Systems Architecture Lead
* **Domain:** Android Native Development (NDK/JNI), Lifecycle Management & State Architecture
* **Mission:** Build the main Android application architecture, manage the multi-threaded native JNI bridge, and run the persistent 24/7 background radio daemon.

#### Detailed Responsibilities & Tasks:
1. **Push-To-Talk (PTT) Hardware & Software State Machine:**
   * Build a deterministic state machine: `IDLE_LISTENING` $\leftrightarrow$ `PTT_CAPTURING` $\leftrightarrow$ `TRANSMITTING` $\leftrightarrow$ `RECEIVING` $\leftrightarrow$ `ALARM_ACTIVE`.
   * Intercept physical hardware volume buttons (`KEYCODE_VOLUME_DOWN`) via `AccessibilityService` or `KeyEvent` dispatchers to toggle PTT even when the screen is locked.
2. **Native C++ JNI Bridge (`native_bridge.cpp`):**
   * Build high-performance JNI methods binding Kotlin to C++ native engines (`initAudioEngine()`, `startRecording()`, `stopRecordingAndTranscribe()`, `synthesizeAndPlay()`).
   * Pass native byte buffers (`DirectByteBuffer`) to eliminate memory copy overhead between Kotlin and C++.
3. **24/7 Persistent Background Foreground Service:**
   * Implement `RadioDaemonService.kt` with persistent notification channel, `START_STICKY`, and partial `WakeLock` (`PARTIAL_WAKE_LOCK`) to prevent Android OS from killing radio listening threads during deep sleep.
4. **Local Audit Database (Room / SQLite):**
   * Build a local chronological database storing all dispatched and received voice messages with timestamps, callsigns, transcripts, byte sizes, and latency metrics.

#### Technical Specifications & Deliverables:
* **Tech Stack:** Kotlin, Android NDK (C++20), CMake, JNI, Android Services & Coroutines, Room Persistence Library.
* **Code Deliverables:**
  * `app/src/main/cpp/native_bridge.cpp`
  * `app/src/main/java/org/isro/itantra/service/RadioDaemonService.kt`
  * `app/src/main/java/org/isro/itantra/domain/PTTStateMachine.kt`
  * `app/src/main/java/org/isro/itantra/data/local/MessageDatabase.kt`
* **Input / Output Contracts:**
  * Exposes reactive `StateFlow<PTTState>` and `SharedFlow<MessageEvent>` to the UI layer.
* **Dependencies & Handoff:** Connects native engines from **Members 1, 2, 3, 4** and provides data feeds for **Member 6**.

---

### 👤 Member 6: Tactical UI/UX, Telemetry Dashboard, Battery Profiler & QA Lead
* **Domain:** User Experience Design, System Benchmarking, Quality Assurance & Hackathon Defense
* **Mission:** Build the military-grade tactical UI, visual live telemetry monitor, energy profiling harness, and manage the 3-minute hackathon winning live pitch.

#### Detailed Responsibilities & Tasks:
1. **Tactical Military-Grade Jetpack Compose UI:**
   * Build a high-contrast dark-mode interface (`#0B0E14` background with `#00E5FF` and `#FF3D00` tactical accents).
   * Features: Large central tactile PTT button with haptic feedback, real-time audio FFT waveform visualizer, active peer radar grid, and quick language selector.
2. **Real-Time Live Jury Telemetry Overlay:**
   * Build an on-screen diagnostic overlay displaying live hardware metrics:
     * `Transmitted Packet Size: 38 Bytes`
     * `Airtime / Transmission Latency: 18 ms`
     * `Bandwidth Saved vs PCM: 99.8%`
     * `Carrier Status: Wi-Fi Direct (P2P-GO)`
3. **Live Demonstration Control Panel (Demo Harness):**
   * Build a hidden developer drawer with test injection buttons:
     * `[Simulate Airplane Mode]`
     * `[Inject 40% Packet Loss]`
     * `[Trigger SOS Max Volume Alarm]`
     * `[Toggle Hindi -> Tamil Translation]`
4. **Energy Profiling & Benchmark Validation:**
   * Profile the app using **Android Studio Energy Profiler** and `top -n 1 | grep org.isro.itantra`.
   * Record and prove that idle listening CPU usage remains strictly **$<3\%$**, satisfying the 20% evaluation rubric.

#### Technical Specifications & Deliverables:
* **Tech Stack:** Jetpack Compose, Material3 Dark Theme, Android Profiler, Battery Historian, JUnit/Espresso.
* **Code Deliverables:**
  * `app/src/main/java/org/isro/itantra/ui/screens/MainWalkieTalkieScreen.kt`
  * `app/src/main/java/org/isro/itantra/ui/components/TacticalPTTButton.kt`
  * `app/src/main/java/org/isro/itantra/ui/components/AudioWaveformVisualizer.kt`
  * `app/src/main/java/org/isro/itantra/ui/components/LiveTelemetryOverlay.kt`
  * `docs/benchmarks/Energy_CPU_Benchmark_Report.pdf`
* **Input / Output Contracts:**
  * Renders state from **Member 5**; injects mock events into **Member 4** & **Member 5** during testing.
* **Dependencies & Handoff:** Owns final app packaging, test verification, and live stage presentation.

---

## 🛠️ Unified System Technology Matrix

| Layer | Technology | Selection Rationale |
| :--- | :--- | :--- |
| **Target OS** | Android 11+ (API 30+) | Universal deployment on budget ₹8,000–₹15,000 smartphones. |
| **UI Framework** | Kotlin + Jetpack Compose | Modern declarative UI, reactive state flow, zero XML boilerplate. |
| **Native Performance Core** | C++20 via Android NDK (JNI) | Zero-overhead DSP, lock-free ring buffers, SIMD vectorization. |
| **Audio Engine** | Google Oboe (AAudio/OpenSL) | Sub-10ms native audio capture and rendering with zero glitching. |
| **VAD Engine** | Silero VAD v5 (ONNX Mobile) | 1.8 MB footprint; <1ms inference per 30ms; keeps idle CPU <3%. |
| **On-Device STT** | AI4Bharat IndicConformer (INT8) | Native Indic phonetics; 10,000+ hrs training; compressed to ~35 MB. |
| **On-Device TTS** | FastPitch + HiFi-GAN Vocoder (INT8)| Natural neural speech synthesis in <150ms on mobile ARM CPU. |
| **Offline Translation (NMT)**| IndicTrans2-Distilled (INT8) | On-device dialect translation without cloud APIs (<25 MB). |
| **Inference Engine** | ONNX Runtime Mobile v1.17+ | Multi-threaded ARM XNNPACK and NNAPI hardware acceleration. |
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

## 📅 10-Day Production Sprint Schedule

```
+----------------------------------------------------------------------------------------------------+
|                                    10-DAY SPRINT SCHEDULE                                          |
+----------------------------------------------------------------------------------------------------+

 Day 1 - 2: Foundation, Interface Freezing & Mock Stubs
 ├── M1: Export Silero VAD & IndicConformer to ONNX; verify inference on desktop.
 ├── M2: Export Indic FastPitch + HiFi-GAN to ONNX; test speech synthesis on Python.
 ├── M3: Define `packet_schema.proto`; compile C++ and Kotlin Lite bindings.
 ├── M4: Build standalone Android Wi-Fi Direct peer discovery test app.
 ├── M5: Scaffold Android Studio monorepo with CMake NDK bridge and JNI header stubs.
 └── M6: Design high-contrast Figma UI assets and build Jetpack Compose theme system.

 Day 3 - 5: Core Engineering & Quantization
 ├── M1: Quantize STT model to INT8 (<38MB); integrate Oboe audio capture ring buffer.
 ├── M2: Quantize TTS model to INT8 (<45MB); implement `STREAM_ALARM` audio track.
 ├── M3: Build IndicTrans2 translation bridge and arithmetic sub-word tokenizer.
 ├── M4: Complete non-blocking async socket server; add Bluetooth RFCOMM fallback.
 ├── M5: Build PTT state machine and foreground service lifecycle handlers.
 └── M6: Implement real-time waveform visualizer and P2P peer radar screen.

 Day 6 - 7: Native Integration & JNI Fusion
 ├── Merge M1 (STT) + M2 (TTS) + M3 (Protocol) into native shared library (`libitantra_core.so`).
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

## 🎤 3-Minute Live Hackathon Demo Script (For Jury Defense)

1. **Act 1: The Airplane Mode Proof (20s):**
   > *"Judges, we have placed both phones in complete Airplane Mode with zero cellular SIM, zero Wi-Fi routers, and zero cloud connectivity."*
2. **Act 2: The Instant Voice Relay (40s):**
   > *(Speak into Phone A in Hindi)*: *"सेक्टर 4 में तुरंत सहायता भेजो!"*  
   > *(Phone B across the room receives the 38-byte packet in <300ms and speaks aloud)*  
   > *"We just transmitted a voice command using only 38 bytes of data — a 99.8% bandwidth reduction compared to standard audio."*
3. **Act 3: The Emergency Mute Override (40s):**
   > *"Phone B is currently set to Do Not Disturb and Mute. When we transmit an SOS Alert, our system accesses hardware `STREAM_ALARM` focus, forcing the phone to sound the alarm at maximum volume."*
4. **Act 4: The 20% Evaluation Metric Proof (30s):**
   > *(Point to the live telemetry on screen)*: *"Notice the CPU monitor: while the room is silent, our Silero VAD keeps CPU utilization under 2.8%, ensuring multi-day battery life in the field."*
