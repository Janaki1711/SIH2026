# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Sponsoring Agency: Indian Space Research Organisation (ISRO)

> **Offline, Edge-Deployable, Multilingual Semantic Walkie-Talkie and Long-Range Mesh Transceiver with Zero-Bitrate Voice Cloning and Real-Time Indic Translation.**

---

## 👥 Team Roster & Role Assignment Table

| Member | Assigned Name | Primary Role | Domain & Core Module | Key Tools & Technologies | Major Deliverable Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Member 1** | **Chhavi** | AI Speech Recognition (STT) & DSP Lead | Audio Ingestion, Silero VAD & IndicConformer STT | PyTorch, Google Oboe, ONNX Runtime Mobile, C++20, NDK | `libaudio_stt_core.so`, `indic_stt_int8.onnx`, `silero_vad.onnx` |
| **Member 2** | **Vaibhav Senior** | Neural Speech Synthesis (TTS) & Audio Lead | Edge Indic TTS, Voice Tone Cloner & Audio Playback | FastPitch, HiFi-GAN, Android `STREAM_ALARM`, Oboe, C++ | `libaudio_tts_core.so`, `indic_fastpitch_int8.onnx`, `AlarmAudioRouter.kt` |
| **Member 3** | **Parth Karpe** | Semantic Compression & TinyML Agent Lead | Multi-Task TinyML Agent, IndicTrans2 & Protobuf Framer | Protocol Buffers (Lite), `IndicBERT-Tiny`, `IndicTrans2`, AES-128 | `packet_schema.proto`, `multitask_agent_int8.onnx`, `indic_trans_int8.onnx` |
| **Member 4** | **M Janaki** | P2P Wireless Transport & WFB-ng Protocol Lead | WFB-ng Resilient UDP + FEC, Wi-Fi Direct, Bluetooth & Mesh | Android `WifiP2pManager`, Libsodium ChaCha20, Reed-Solomon FEC, Java NIO | `WfbngTransportManager.kt`, `ReedSolomonFEC.kt`, `WifiP2pTransport.kt` |
| **Member 5** | **Nupur** | Native Android Core & Database Lead | PTT State Machine, Foreground Daemon & JNI Bridge | Kotlin, JNI, CMake, Room (SQLite), Android Foreground Service | `native_bridge.cpp`, `RadioDaemonService.kt`, `MessageDatabase.kt` |
| **Member 6** | **Vaibhav Junior** | Tactical UI/UX & Benchmark/Pitch Lead | Jetpack Compose UI, Telemetry Overlay & QA Harness | Jetpack Compose, Material 3, Android Studio Profiler | `MainWalkieTalkieScreen.kt`, `LiveTelemetryOverlay.kt`, Benchmark Report |

---

## 🎯 Executive Summary & Core Principle

Standard voice streaming (Opus, PCM, AMR) requires **16 to 128 kbps**, collapsing completely under RF interference, satellite link bottlenecks, and disaster-induced infrastructure blackouts. **iTantra** implements **Semantic Voice Transmission (Voice → Text → RF → Voice)** directly on edge hardware, enabling **100% intelligible two-way communication at <50 bps** with zero cellular network or internet infrastructure.

1. **2,000× Data Compression (38 Bytes vs 160,000 Bytes):** We convert voice to meaning on-device, transmit tiny micro-packets across radio links, and re-synthesize speech locally.
2. **Zero-Bitrate Voice & Emotion Cloning:** Extracts a 16-byte acoustic vector so the synthesized speech preserves the sender's exact voice timbre, pitch, and panicked emergency tone.
3. **Universal Indic "Babel-Fish" Voice Bridge:** A rescue worker speaks Hindi in Uttarakhand; a doctor in Kerala hears it spoken aloud in Malayalam in <300 ms offline.
4. **WFB-ng Indestructible Radio Protocol:** Uses connectionless UDP and Reed-Solomon Forward Error Correction (FEC) to survive **40% packet drops with zero lag**.
5. **Zero-Friction Consumer-Grade UX:** Open the app → Phones auto-discover in 3 seconds → Press the haptic PTT button and speak. Zero manual IP typing or pairing required.
6. **Opportunistic Local-to-Global Gateway:** 100% offline by default, but if any single phone or drone catches a weak satellite/2G link, it bridges the entire disaster network to National Command HQ.

---

## 🔄 End-to-End System Execution Flow

```
====================================================================================================
                                      SENDER PHONE (TRANSMITTER)
====================================================================================================

 [Step 1: User Presses Tactical PTT Button] (Native Android Runtime)
    │   • Single-tap haptic trigger; activates audio ingestion stream.
    ▼
 [Step 2: Google Oboe Native Audio Capture] (Acoustic Ingestion Subsystem)
    │   • Ingests raw 16kHz 16-bit Mono PCM audio in 30ms lock-free circular ring buffers.
    ▼
 [Step 3: Silero VAD Gatekeeper (<1ms)] (Acoustic Ingestion Subsystem)
    │   • Detects human voice onset/cutoff; keeps idle CPU <2.8% during silence.
    ▼
 [Step 4: AI4Bharat IndicConformer STT Engine (INT8 ONNX)] (Acoustic Ingestion Subsystem)
    │   • Converts Hindi/Indic voice into raw text transcript in <180ms.
    ▼
 [Step 5: Multi-Task TinyML Agent (IndicBERT-Tiny)] (Semantic Intelligence Subsystem)
    │   • Task A: Snaps local geographic landmarks ("Tolan care" -> "Tolankere GeoID: 0x4F2A").
    │   • Task B: Extracts Intent & Action Codes ("RESCUE_REQUEST | COUNT: 5 | HAZARD: FLOOD").
    │   • Task C: Evaluates Acoustic Emotion -> Classifies urgency as "CRITICAL_PANIC_SOS (0x03)".
    ▼
 [Step 6: 3-Tier Compression & Protobuf Packaging] (Semantic Intelligence Subsystem)
    │   • Tier 1 (Semantic Macro): 6 - 8 Bytes.
    │   • Tier 2 (Structured Frame): 18 - 22 Bytes.
    │   • Tier 3 (Arithmetic Phoneme Fallback): 35 - 38 Bytes.
    │   • Total packet size: ONLY 6 to 38 Bytes!
    ▼
 [Step 7: Local Database Insertion (Room / SQLite)] (Storage Subsystem)
    │   • Logs message in local SQLite flight black-box with status "TRANSMITTING".
    ▼
 [Step 8: WFB-ng Radio Transmitter & FEC Encoder] (Wireless Transport Subsystem)
    │   • Encrypts via Libsodium ChaCha20-Poly1305.
    │   • Generates Reed-Solomon (8, 4) FEC Parity Blocks (survives 40% packet drops).
    │   • Transmits over Connectionless UDP Wi-Fi Direct / BLE Mesh.
    │
═════════════════════════════════════ WIRELESS RF HOP (<20 ms) ═════════════════════════════════════
    │
====================================================================================================
                                      RECEIVER PHONE (LISTENER)
====================================================================================================
    │
    ▼
 [Step 9: WFB-ng Receiver Daemon & FEC Decoder] (Wireless Transport Subsystem)
    │   • Receives UDP datagrams; decrypts with Libsodium.
    │   • Reconstructs dropped packets via Reed-Solomon FEC without retransmission delay.
    ▼
 [Step 10: Protobuf Unpacker & IndicTrans2 Translation] (Semantic Intelligence Subsystem)
    │   • Unpacks 6B-38B frame; translates text from Hindi to Tamil/Kannada in <80ms.
    ▼
 [Step 11: Local Database Sync & UI Telemetry Update] (Storage Subsystem & UI)
    │   • Inserts received packet into local SQLite MessageAuditLog.
    │   • Updates Jetpack Compose UI (displays text transcript + live 38-byte telemetry card).
    ▼
 [Step 12: On-Device FastPitch + HiFi-GAN TTS Engine] (Neural Synthesis Subsystem)
    │   • Ingests translated text + conditions on the 16-byte prosody vector.
    │   • Synthesizes natural speech reproducing sender's original pitch & frantic urgency in <140ms.
    ▼
 [Step 13: Hardware Priority Audio Playback (STREAM_ALARM)] (Neural Synthesis Subsystem)
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

## 🧩 Modular Engineering: Built in Isolated Parts & Integrated Together

The architecture is cleanly separated into **6 independent technical subsystems**. Each part can be built, compiled, and unit-tested in isolation before being unified into the master Android application.

```
+----------------------------------------------------------------------------------------------------+
|                                   6-PART MODULAR SUBSYSTEM TOPOLOGY                                |
+----------------------------------------------------------------------------------------------------+

  [PART 1: Acoustic Ingestion & Speech-to-Text] ──(Text + Prosody)──> [PART 2: Semantic Compression]
                                                                                   │
                                                                                   ▼ (6B - 38B Frame)
  [PART 4: Neural Synthesis & Voice Cloner] <──(Decoded Text)─── [PART 3: WFB-ng Wireless Mesh]
                         │                                                         ▲
                         │ (Audio Stream)                                          │ (Byte Stream)
                         ▼                                                         ▼
  [PART 5: Native Android Runtime & SQLite DB] <═════════════════> [PART 6: Tactical UI & Telemetry]
```

---

### 🎙️ Member 1: Acoustic Ingestion, Silero VAD & Speech-to-Text Subsystem (Chhavi)
* **Core Function:** Low-latency native audio capture, micro-VAD speech detection gating, and offline quantized Indic phoneme recognition.
* **Component Architecture:**
  1. **Native Audio Capture (`OboeAudioRecorder.cpp` & `AudioRingBuffer.hpp`):**
     * Direct interface with Android's native `AAudio` / `OpenSL ES` drivers via Google Oboe C++.
     * Lock-free circular ring buffer processing 16 kHz 16-bit Mono PCM audio in 30 ms chunks (480 samples).
  2. **Micro-VAD Speech Gatekeeper (`SileroVAD.cpp`):**
     * Integrates the Silero VAD v5 ONNX model (~1.8 MB) executing in $<1	ext{ ms}$ on CPU.
     * Keeps heavy downstream AI models asleep during silence, maintaining idle CPU load strictly below **$<2.8\%$**.
  3. **Quantized Indic STT Engine (`IndicSTTEngine.cpp`):**
     * Runs static INT8 quantized AI4Bharat IndicConformer (~35 MB) using ONNX Runtime Mobile with XNNPACK.
     * CTC greedy decoding outputs transcript text + Language ID in $<180	ext{ ms}$.
* **Artifact Deliverables:** `libaudio_stt_core.so`, `silero_vad.onnx`, `indic_stt_int8.onnx`.

---

### 🗜️ Member 2: Semantic Compression, Multi-Task TinyML & Binary Serialization Subsystem (Parth)
* **Core Function:** Converts raw text transcripts into compact binary semantic tokens, extracts out-of-vocabulary local landmarks and emotions, and handles dialect translation.
* **Component Architecture:**
  1. **Multi-Task TinyML Agent (`MultiTaskAgent.cpp`):**
     * Quantized `IndicBERT-Tiny-INT8` / `MobileBERT` model ($<22	ext{ MB}$, $<35	ext{ ms}$ inference).
     * **Local Geographic Entity Resolution:** Uses Soundex and a local geographic prefix trie to snap misspelled local landmarks (*"Tolan care" → Tolankere GeoID: `0x4F2A`*).
     * **Intent & Action Extractor:** Maps recognized voice intents into single-byte macro action codes (`EVACUATE`, `FLOOD`, `BOAT`).
     * **Vocal Urgency Classifier:** Extracts emotion from speech features, setting Urgency to `Routine`, `Tactical`, or `Critical SOS`.
  2. **Offline Indic-to-Indic Translation Bridge (`IndicTranslationEngine.cpp`):**
     * Distilled `IndicTrans2-INT8` (~24 MB) executes dialect-to-dialect translation (e.g., Hindi $\leftrightarrow$ Tamil/Kannada in $<80	ext{ ms}$).
  3. **3-Tier Compression & Protobuf Framer (`PacketFramer.cpp`):**
     * Assembles binary frames: Tier 1 (Semantic Macro: 6–8B), Tier 2 (Structured Frame: 18–22B), Tier 3 (Arithmetic Phoneme Fallback: 35–38B).
     * Appends CRC16-CCITT checksum for frame validation.
* **Artifact Deliverables:** `packet_schema.proto`, `multitask_agent_int8.onnx`, `indic_trans_int8.onnx`, `libsemantic_protocol.so`.

---

### 📡 Member 3: WFB-ng Wireless Transport, Reed-Solomon FEC & Mesh Subsystem (Janaki)
* **Core Function:** 100% offline, connectionless radio transmission, Reed-Solomon error correction, Libsodium encryption, and multi-hop range extension.
* **Component Architecture:**
  1. **Reed-Solomon Forward Error Correction Engine (`ReedSolomonFEC.kt`):**
     * Implements Block FEC: Generates 4 parity blocks for every 8 data packets ($8$ data $+ 4$ parity).
     * Reconstructs dropped or corrupted speech packets with **zero retransmission delay**, surviving up to **40% RF packet loss**.
  2. **Connectionless UDP Wi-Fi Direct Transport (`WifiP2pTransport.kt`):**
     * Autonomous peer discovery (DNS-SD `_itantra_radio._tcp`) and Group Owner (GO) negotiation.
     * High-throughput UDP datagram socket server on port `8988`, eliminating TCP connection and head-of-line blocking delays.
  3. **Master Transceiver Controller (`WfbngTransportManager.kt`):**
     * Encrypts outgoing payloads with Libsodium `crypto_aead_chacha20poly1305`.
     * Manages **Autonomous Dual-Mode Failover**: Automatically switches to Bluetooth RFCOMM / BLE in $<50	ext{ ms}$ if Wi-Fi Direct RSSI drops below $-85	ext{ dBm}$.
  4. **7-Hop Mesh Store-and-Forward Router (`MeshRelayRouter.kt`):**
     * Multi-hop store-and-forward relay with a 64-entry LRU ring of packet hashes to prevent broadcast storms, extending range across intermediate nodes from 50m to 500m–5km.
* **Artifact Deliverables:** `WfbngTransportManager.kt`, `ReedSolomonFEC.kt`, `WifiP2pTransport.kt`, `BluetoothTransport.kt`.

---

### 🔊 Member 4: Neural Speech Synthesis, Voice Cloning & Emergency Playback Subsystem (Vaibhav snr.)
* **Core Function:** Local speech synthesis from text tokens, zero-bitrate voice timbre and emotion cloning, and hardware-priority audio dispatching.
* **Component Architecture:**
  1. **Quantized Neural Indic Speech Synthesis (`IndicTTSEngine.cpp`):**
     * AI4Bharat `Indic-FastPitch` (Mel-Spectrogram predictor) and `HiFi-GAN` neural vocoder in ONNX INT8 ($<42	ext{ MB}$ total).
     * Executes in $<140	ext{ ms}$ for a 5-second sentence on mobile ARM CPUs.
  2. **Zero-Bitrate Voice Identity & Emotion Cloner (`VoiceToneCloner.cpp`):**
     * Ingests the 16-byte Prosody Vector ($F_0$ pitch contour + timbre $d$-vector + urgency level).
     * Conditions FastPitch duration and pitch predictors to synthesize speech that preserves the sender's original voice pitch and panicked emergency urgency.
  3. **Hardware Priority Emergency Audio Router (`AlarmAudioRouter.kt`):**
     * Routes SOS alerts through `AudioManager.STREAM_ALARM` with `AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE` and `FLAG_AUDIBILITY_ENFORCED`.
     * Forces speaker output to **100% maximum volume**, overriding Android Do Not Disturb and Mute settings.
* **Artifact Deliverables:** `libaudio_tts_core.so`, `indic_fastpitch_int8.onnx`, `hifigan_vocoder_int8.onnx`, `AlarmAudioRouter.kt`.

---

### 🧠 Member 5: Native Android Runtime, State Machine & Local Storage Subsystem (Nupur)
* **Core Function:** Application lifecycle coordination, hardware button interception, zero-copy JNI memory bridge, and embedded SQLite black-box logging.
* **Component Architecture:**
  1. **Zero-Copy JNI Native Bridge (`native_bridge.cpp`):**
     * High-performance JNI bindings using `DirectByteBuffer` to pass audio and binary frames between Kotlin and C++ without JVM garbage collection pauses.
  2. **Deterministic PTT State Machine (`PTTStateMachine.kt`):**
     * Manages runtime states: `IDLE_LISTENING` $\leftrightarrow$ `PTT_CAPTURING` $\leftrightarrow$ `TRANSMITTING` $\leftrightarrow$ `RECEIVING` $\leftrightarrow$ `ALARM_ACTIVE`.
     * Intercepts physical hardware volume buttons (`KEYCODE_VOLUME_DOWN`) to toggle PTT even when the screen is locked.
  3. **24/7 Persistent Radio Daemon (`RadioDaemonService.kt`):**
     * Android Foreground Service with `START_STICKY`, persistent notification, and `PARTIAL_WAKE_LOCK` keeping the radio receiver active around the clock.
  4. **Local Room SQLite Black-Box Database (`MessageDatabase.kt` & `MessageDao.kt`):**
     * Manages `MessageAuditLog` (flight black box), `MeshPeerRegistry` (neighbor nodes and signal quality), and `EmergencyCodebook` (offline macro lookups).
* **Artifact Deliverables:** `native_bridge.cpp`, `RadioDaemonService.kt`, `PTTStateMachine.kt`, `MessageDatabase.kt`.

---

### 📱 Member 6: Tactical UI/UX, Peer Radar & Live Telemetry Subsystem (Vaibhav Jr.)
* **Core Function:** Modern, high-contrast tactical user interface, live hardware telemetry HUD, peer discovery radar, and developer diagnostic controls.
* **Component Architecture:**
  1. **Tactical Military-Grade Jetpack Compose UI (`MainWalkieTalkieScreen.kt`):**
     * High-contrast dark palette (`#0B0E14` with `#00E5FF` cyan active and `#FF3D00` alert accents).
     * Central tactile PTT button with haptic feedback and dynamic FFT audio waveform visualizer (`AudioWaveformVisualizer.kt`).
  2. **Live Hardware Telemetry HUD (`LiveTelemetryOverlay.kt`):**
     * Real-time diagnostic card displaying: `Payload Size (6-38 Bytes)`, `Airtime Latency (18 ms)`, `Bandwidth Saved (99.8%)`, `WFB-ng FEC Parity (4 Blocks)`, `Carrier (Wi-Fi Direct / BT)`.
  3. **Diagnostic Test Panel (`DemoInjectionDrawer.kt`):**
     * Developer control drawer with one-touch triggers: `[Simulate Airplane Mode]`, `[Inject 40% Packet Loss]`, `[Trigger SOS Max Volume Alarm]`, `[Toggle Hindi -> Tamil]`.
* **Artifact Deliverables:** `MainWalkieTalkieScreen.kt`, `LiveTelemetryOverlay.kt`, `DemoInjectionDrawer.kt`.

---

## 🔗 Integration Plan: How All Parts Fuse Together

```
====================================================================================================
                                      MASTER INTEGRATION PIPELINE
====================================================================================================

 PHASE 1: C++ Native Engine Compilation (Member 1 + 2 + 4)
 ├── Compile Oboe Audio Ingestion + Silero VAD + IndicConformer STT.
 ├── Compile Multi-Task TinyML Agent + IndicTrans2 + Protobuf Framer.
 ├── Compile FastPitch Mel-Model + HiFi-GAN Vocoder.
 └── Output: Single unified C++ shared library -> `libitantra_core.so`

 PHASE 2: Native-to-Kotlin Binding via JNI (Member 1, 2, 4 -> Part 5)
 ├── Wire `native_bridge.cpp` to expose zero-copy JNI methods to Kotlin:
 │   ├── `nativeStartCapture()`, `nativeStopAndTranscribe()`
 │   ├── `nativeProcessTinyML()`, `nativeFramePacket()`
 │   └── `nativeSynthesizeAudio()`, `nativePlayAlarm()`

 PHASE 3: Network & Database Attachment (Member 3 + 5)
 ├── Connect `WfbngTransportManager.kt` to `RadioDaemonService.kt`.
 ├── Outgoing binary frames -> Reed-Solomon FEC -> UDP Socket Send -> Log in Room DB.
 └── Incoming UDP Datagrams -> Libsodium Decrypt -> FEC Reconstruct -> Log in Room DB.

 PHASE 4: UI & StateFlow Reactivity (Member 5 + 6)
 ├── Bind `PTTStateMachine.kt` to `TacticalPTTButton.kt` (Press/Release events).
 ├── Bind incoming `MessageAuditLog` stream to `MainWalkieTalkieScreen.kt` message feed.
 └── Bind live RF metrics (RSSI, Bytes, Latency) to `LiveTelemetryOverlay.kt`.

 PHASE 5: End-to-End System Validation
 └── Full loop on 2 physical Android phones: Speak -> VAD -> STT -> TinyML -> UDP RF -> TTS -> Speaker.
```

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
  
  bytes compressed_payload = 7;  // Tier 1 (6B), Tier 2 (18B), or Tier 3 (38B)
  bytes prosody_vector = 8;      // 16-byte pitch & speaker identity vector
  uint32 crc16_checksum = 9;     // Error detection checksum
}
```
