# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Organization: ISRO

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

## 🚨 Problem Statement & The Need

In defense field operations, satellite communications (SATCOM), high-frequency (HF) skywave radio, and disaster relief zones (floods, earthquakes, landslides):
1. **Zero Infrastructure:** Cellular towers and internet backbones fail or do not exist.
2. **Audio Packet Drop:** Traditional audio codecs stutter and fail when packet loss exceeds 25%.
3. **Severe Bandwidth Limits:** Satellite channels (e.g., ISRO NavIC Short Messaging) offer sub-frame capacities of only 12–16 bytes per burst.
4. **Linguistic Barriers:** Multi-state first responders and coastal communities speak distinct regional Indian languages.
5. **Battery Constraints:** Continuous listening on edge devices drains phone batteries within 2–3 hours.

---

## 💡 Key Technical Innovations

1. **2,000× Data Reduction:** Compresses 5 seconds of audio (160,000 bytes) into a single **40-byte** binary payload.
2. **Zero-Bitrate Voice & Emotion Cloning:** Attaches a 16-byte prosody/speaker vector so the receiver synthesizes speech in the **sender's original voice, pitch, and emotional urgency**.
3. **<3% Idle CPU Consumption (VAD Gating):** Lightweight Silero VAD keeps heavy neural networks dormant during silence, solving the critical battery metric.
4. **Offline Indic-to-Indic Translation Bridge:** Instant on-device translation across 10+ Indian dialects (e.g., Tamil speech synthesized as Hindi audio).
5. **Hardware Priority Alerting (`STREAM_ALARM`):** Life-safety SOS alerts bypass Android Do-Not-Disturb and Silent modes at 100% volume.
6. **Dual-Tier Physical Radio Support:** Seamlessly transmits over Wi-Fi Direct, Bluetooth RFCOMM, BLE Mesh, and NavIC/LoRa framing.

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

## 👥 6-Member Balanced Work Breakdown

```
                                  6-MEMBER WORK ALLOCATION
                                  ------------------------
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 1] Audio Ingestion, Silero VAD Gatekeeper & IndicConformer STT Engine            |
  +--------------------------------------------+--------------------------------------------+
                                               | (Decoded Transcript + Lang ID)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 3] Semantic Compression, Indic Translation Bridge & Binary Protobuf Framer       |
  +--------------------------------------------+--------------------------------------------+
                                               | (Packaged 40-Byte Binary Frame)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 4] P2P Wireless Transport Layer (Wi-Fi Direct & Bluetooth RFCOMM Sockets)        |
  +--------------------------------------------+--------------------------------------------+
                                               | (Wireless Hop to Receiver Phone)
                                               v
  +-----------------------------------------------------------------------------------------+
  | [MEMBER 2] On-Device Indic TTS Engine, Voice Tone Cloner & STREAM_ALARM Playback        |
  +-----------------------------------------------------------------------------------------+
                                               ^
                                               |
  +--------------------------------------------+--------------------------------------------+
  | [MEMBER 5] Native Android App, PTT State Machine & NDK/JNI Core Integration              |
  +--------------------------------------------+--------------------------------------------+
                                               ^
                                               |
  +--------------------------------------------+--------------------------------------------+
  | [MEMBER 6] Tactical UI/UX, Telemetry Dashboard, Battery Benchmarking & Demo Harness     |
  +-----------------------------------------------------------------------------------------+
```

### Member 1: Audio Ingestion, VAD Gatekeeper & Indic STT Pipeline
* **Role:** AI Speech Recognition & DSP Engineer
* **Deliverables:** `libaudio_stt_core.so` + `indic_stt_int8.onnx` + Google Oboe microphone bridge.
* **Tasks:** Ingest 16 kHz 16-bit PCM audio; run Silero VAD gatekeeper (<1ms); execute INT8 quantized IndicConformer speech recognition.

### Member 2: Edge Indic TTS, Voice Tone Cloner & Audio Playback Engine
* **Role:** Neural Audio Synthesis & Playback Engineer
* **Deliverables:** `libaudio_tts_core.so` + `indic_tts_int8.onnx` + `STREAM_ALARM` audio renderer.
* **Tasks:** Synthesize Indic speech from text tokens; inject 16-byte prosody vector for voice cloning; route emergency alerts through hardware alarm stream.

### Member 3: Semantic Compression, Translation Bridge & Protobuf Framer
* **Role:** Edge NLP, Cryptography & Serialization Engineer
* **Deliverables:** `libsemantic_protocol.so` + compiled Protobuf classes + `IndicTrans2` INT8 translation bridge.
* **Tasks:** Build Protobuf binary packaging schema with CRC16; translate across Indic languages; compress sentences to 15–30 bytes.

### Member 4: P2P Wireless Transport Layer (Wi-Fi Direct & Bluetooth)
* **Role:** Embedded Systems & Wireless Networking Engineer
* **Deliverables:** `P2PTransportManager.kt` service managing peer discovery and non-blocking asynchronous sockets.
* **Tasks:** Implement Wi-Fi Direct Group Owner auto-election; build dual-mode Bluetooth RFCOMM fallback; guarantee packet delivery with selective ACK.

### Member 5: Native Android App, PTT State Machine & NDK Integration
* **Role:** Native Android Architecture & Systems Lead
* **Deliverables:** Compiled Android APK architecture + JNI bindings + 24/7 background foreground daemon.
* **Tasks:** Build hardware/software Push-To-Talk state machine; manage WakeLocks and background persistence; link C++ libraries to Kotlin.

### Member 6: Tactical UI/UX, Telemetry Dashboard, QA & Live Demo Harness
* **Role:** UI/UX Developer, Performance Profiler & Integration Lead
* **Deliverables:** Jetpack Compose tactical UI + live telemetry monitor + automated test harness.
* **Tasks:** Build high-contrast PTT interface; display real-time latency and bitrate savings; verify <3% idle CPU load using Android Profiler.

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
