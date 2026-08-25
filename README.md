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
    [Voice Spoken] -> [STT Transcription] -> [Tokenize (38B)] -> [SQLite DB Save] -> [Wi-Fi/BT TX]

 3. RECEPTION STATE (Background Daemon):
    [RF Packet Rx] -> [CRC16 Check] -> [NMT Translate] -> [SQLite DB Save] -> [TTS Synthesize] -> [Speaker]

 4. EMERGENCY OVERRIDE STATE (SOS Priority):
    [Priority == 2] -> [Request AudioManager.STREAM_ALARM] -> [Force Max Volume] -> [Play Non-Duckable]
```

---

## 👥 6-Member Balanced Work Allocation

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

### Member 1: Audio Ingestion, VAD Gatekeeper & Indic STT Pipeline
* **Deliverables:** `libaudio_stt_core.so` + `indic_stt_int8.onnx` + Google Oboe microphone bridge.
* **Tasks:** Ingest 16 kHz 16-bit PCM audio; run Silero VAD gatekeeper (<1ms); execute INT8 quantized IndicConformer speech recognition.

### Member 2: Edge Indic TTS, Voice Tone Cloner & Audio Playback Engine
* **Deliverables:** `libaudio_tts_core.so` + `indic_tts_int8.onnx` + `STREAM_ALARM` audio renderer.
* **Tasks:** Synthesize Indic speech from text tokens; inject 16-byte prosody vector for voice cloning; route emergency alerts through hardware alarm stream.

### Member 3: Semantic Compression, Translation Bridge & Protobuf Framer
* **Deliverables:** `libsemantic_protocol.so` + compiled Protobuf classes + `IndicTrans2` INT8 translation bridge.
* **Tasks:** Build Protobuf binary packaging schema with CRC16; translate across Indic languages; compress sentences to 15–30 bytes.

### Member 4: P2P Wireless Transport Layer (Wi-Fi Direct & Bluetooth)
* **Deliverables:** `P2PTransportManager.kt` service managing peer discovery and non-blocking asynchronous sockets.
* **Tasks:** Implement Wi-Fi Direct Group Owner auto-election; build dual-mode Bluetooth RFCOMM fallback; guarantee packet delivery with selective ACK.

### Member 5: Native Android App, PTT State Machine & NDK Integration
* **Deliverables:** Compiled Android APK architecture + JNI bindings + 24/7 background foreground daemon.
* **Tasks:** Build hardware/software Push-To-Talk state machine; manage WakeLocks and background persistence; link C++ libraries to Kotlin.

### Member 6: Tactical UI/UX, Telemetry Dashboard, QA & Live Demo Harness
* **Deliverables:** Jetpack Compose tactical UI + live telemetry monitor + automated test harness.
* **Tasks:** Build high-contrast PTT interface; display real-time latency and bitrate savings; verify <3% idle CPU load using Android Profiler.

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
