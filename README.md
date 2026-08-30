# iTantra — Indian Multilingual Neural Transceiver for Low-Bitrate Links
### Smart India Hackathon (SIH 2026) | Problem Statement: SIH26173 | Sponsoring Agency: Indian Space Research Organisation (ISRO)

> **The World's First 100% Offline, Multi-Task TinyML-Powered Semantic Walkie-Talkie & Long-Range Mesh Transceiver with Zero-Bitrate Voice Cloning and Real-Time Indic Translation.**

---

## 🌟 What Makes iTantra Completely Unique & Unprecedented?

Existing walkie-talkies (Motorola, Zello) stream **heavy raw audio (16,000 to 128,000 bps)** that collapses under RF noise, while existing mesh apps (BitChat, Meshtalk) are **text-only typing chats**.

**iTantra creates an entirely new category:** An **AI-Powered Semantic Voice Transceiver** that delivers:
1. **2,000× Data Compression (38 Bytes vs 160,000 Bytes):** We convert voice to meaning on-device, transmit tiny micro-packets across radio links, and re-synthesize speech locally.
2. **Zero-Bitrate Voice & Emotion Cloning:** The receiver doesn't hear a monotone robot. We extract a 16-byte acoustic vector so the synthesized speech **preserves the sender's exact voice timbre, pitch, and panicked emergency tone**.
3. **Universal Indic "Babel-Fish" Voice Bridge:** A rescue worker speaks Hindi in Uttarakhand; a doctor in Kerala hears it spoken aloud in Malayalam in $<300	ext{ ms}$ offline.
4. **WFB-ng Indestructible Radio Protocol:** Uses connectionless UDP and Reed-Solomon Forward Error Correction (FEC) to survive **40% packet drops with zero lag**.
5. **Zero-Friction, Consumer-Grade UX:** Open the app $ightarrow$ Phones auto-discover in 3 seconds $ightarrow$ Press the haptic PTT button and speak. Zero manual IP typing or pairing required.
6. **Opportunistic Local-to-Global Gateway:** 100% offline by default, but if any single phone or drone catches a weak satellite/2G link, it bridges the entire disaster network to National Command HQ!

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

## 🔄 How the Entire System Works (Step-by-Step Technical Flow)

```
====================================================================================================
                                      SENDER PHONE (TRANSMITTER)
====================================================================================================

 [Step 1: User Presses Tactical PTT Button] (Member 5: Nupur & Member 6: Vaibhav Junior)
    │   • Single-tap haptic trigger; activates audio ingestion stream.
    ▼
 [Step 2: Google Oboe Native Audio Capture] (Member 1: Chhavi)
    │   • Ingests raw 16kHz 16-bit Mono PCM audio in 30ms lock-free circular ring buffers.
    ▼
 [Step 3: Silero VAD Gatekeeper (<1ms)] (Member 1: Chhavi)
    │   • Detects human voice onset/cutoff; keeps idle CPU <2.8% during silence.
    ▼
 [Step 4: AI4Bharat IndicConformer STT Engine (INT8 ONNX)] (Member 1: Chhavi)
    │   • Converts Hindi/Indic voice into raw text transcript in <180ms.
    ▼
 [Step 5: Multi-Task TinyML Agent (IndicBERT-Tiny)] (Member 3: Parth Karpe)
    │   • Task A: Snaps local geographic landmarks ("Tolan care" -> "Tolankere GeoID: 0x4F2A").
    │   • Task B: Extracts Intent & Action Codes ("RESCUE_REQUEST | COUNT: 5 | HAZARD: FLOOD").
    │   • Task C: Evaluates Acoustic Emotion -> Classifies urgency as "CRITICAL_PANIC_SOS (0x03)".
    ▼
 [Step 6: 3-Tier Compression & Protobuf Packaging] (Member 3: Parth Karpe)
    │   • Tier 1 (Semantic Macro): 6 - 8 Bytes.
    │   • Tier 2 (Structured Frame): 18 - 22 Bytes.
    │   • Tier 3 (Arithmetic Phoneme Fallback): 35 - 38 Bytes.
    │   • Total packet size: ONLY 6 to 38 Bytes!
    ▼
 [Step 7: Local Database Insertion (Room / SQLite)] (Member 5: Nupur)
    │   • Logs message in local SQLite flight black-box with status "TRANSMITTING".
    ▼
 [Step 8: WFB-ng Radio Transmitter & FEC Encoder] (Member 4: M Janaki)
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
 [Step 9: WFB-ng Receiver Daemon & FEC Decoder] (Member 4: M Janaki)
    │   • Receives UDP datagrams; decrypts with Libsodium.
    │   • Reconstructs dropped packets via Reed-Solomon FEC without retransmission delay.
    ▼
 [Step 10: Protobuf Unpacker & IndicTrans2 Translation] (Member 3: Parth Karpe)
    │   • Unpacks 6B-38B frame; translates text from Hindi to Tamil/Kannada in <80ms.
    ▼
 [Step 11: Local Database Sync & UI Telemetry Update] (Member 5: Nupur & Member 6: Vaibhav Junior)
    │   • Inserts received packet into local SQLite MessageAuditLog.
    │   • Updates Jetpack Compose UI (displays text transcript + live 38-byte telemetry card).
    ▼
 [Step 12: On-Device FastPitch + HiFi-GAN TTS Engine] (Member 2: Vaibhav Senior)
    │   • Ingests translated text + conditions on the 16-byte prosody vector.
    │   • Synthesizes natural speech reproducing sender's original pitch & frantic urgency in <140ms.
    ▼
 [Step 13: Hardware Priority Audio Playback (STREAM_ALARM)] (Member 2: Vaibhav Senior)
        • For SOS alerts: Bypasses Android Mute / Do Not Disturb at 100% volume.
        • Speaks aloud into the receiver's ear!
```

---

## 🗄️ Local Database Architecture (Offline Embedded SQLite / Room)

Managed by **Member 5: Nupur**, the local database serves as the **Tactical Black Box**:

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

---

### 👤 Member 1 (Chhavi): Audio Ingestion, Silero VAD & On-Device Indic STT Lead
* **Domain:** AI Speech Recognition, Digital Signal Processing (DSP) & Edge Acceleration
* **Mission:** Ingest low-latency raw microphone audio, execute micro-VAD speech gating to keep idle CPU $<3\%$, and run INT8 quantized Indic speech recognition offline.

#### Exact Tools & Compilers:
* PyTorch 2.2+, ONNX Runtime Mobile C++ v1.17+, Google Oboe C++ Library (v1.8+), Android NDK r26c, CMake 3.22+, Python 3.10+.
* Models: Silero VAD v5 ONNX (~1.8 MB), AI4Bharat `IndicConformer` INT8 (~35 MB).

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/audio/OboeAudioRecorder.cpp` & `AudioRingBuffer.hpp`:** Lock-free 16 kHz 16-bit Mono PCM circular ring buffer processing 30 ms chunks.
2. **`app/src/main/cpp/ml/SileroVAD.cpp`:** Silero VAD gatekeeper executing in $<1	ext{ ms}$, enforcing silence thresholding to keep idle CPU $<2.8\%$.
3. **`app/src/main/cpp/ml/IndicSTTEngine.cpp`:** C++ ONNX Runtime wrapper running quantized IndicConformer with CTC decoding.
4. **Deliverables:** `libaudio_stt_core.so`, `silero_vad.onnx`, `indic_stt_int8.onnx`.

---

### 👤 Member 2 (Vaibhav Senior): On-Device Indic TTS, Voice Tone Cloner & Audio Playback Lead
* **Domain:** Neural Acoustic Modeling, Speech Synthesis & Android Audio Framework
* **Mission:** Reconstruct natural Indic speech from text packets, inject speaker pitch/emotion via a 16-byte vector, and enforce non-interruptible `STREAM_ALARM` playback.

#### Exact Tools & Compilers:
* PyTorch, FastPitch, HiFi-GAN Vocoder, ONNX Runtime Mobile C++, Android `AudioManager`, Google Oboe Player.
* Models: AI4Bharat `Indic-FastPitch` INT8 (~28 MB), `HiFi-GAN` Vocoder INT8 (~14 MB).

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/ml/IndicTTSEngine.cpp`:** FastPitch + HiFi-GAN ONNX synthesis pipeline executing in $<140	ext{ ms}$.
2. **`app/src/main/cpp/ml/VoiceToneCloner.cpp`:** Conditions FastPitch duration/pitch predictors on the 16-byte Prosody Vector ($F_0$ contour + timbre + urgency).
3. **`app/src/main/java/org/isro/itantra/audio/AlarmAudioRouter.kt`:** Routes SOS alerts through `AudioManager.STREAM_ALARM` at 100% volume, bypassing DND and Mute.
4. **Deliverables:** `libaudio_tts_core.so`, `indic_fastpitch_int8.onnx`, `hifigan_vocoder_int8.onnx`.

---

### 👤 Member 3 (Parth Karpe): Semantic Compression, Multi-Task TinyML Agent & Serialization Lead
* **Domain:** NLP Tokenization, Multi-Task Machine Learning, Information Theory & Cryptography
* **Mission:** Deploy the Multi-Task TinyML Agent to resolve local landmarks (*Hubballi, Tolankere*) and emotions, translate between Indian dialects, and manage 3-tier binary framing.

#### Exact Tools & Compilers:
* Google Protocol Buffers Lite 3.25+, Python `sentencepiece`, `IndicBERT-Tiny`, `IndicTrans2-Distilled-INT8`, Libsodium.
* Models: `multitask_agent_int8.onnx` (~22 MB), `indic_trans_int8.onnx` (~24 MB).

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/ml/MultiTaskAgent.cpp`:** Evaluates Intent, extracts Local Landmark GeoIDs via phonetic Soundex matching, and classifies emotion urgency.
2. **`app/src/main/cpp/ml/IndicTranslationEngine.cpp`:** On-device Indic-to-Indic translation in $<80	ext{ ms}$.
3. **`proto/packet_schema.proto` & `PacketFramer.cpp`:** Assembles 3-tier binary frames (Tier 1: 6B, Tier 2: 18B, Tier 3: 38B) with CRC16.
4. **Deliverables:** `packet_schema.proto`, `multitask_agent_int8.onnx`, `indic_trans_int8.onnx`, `libsemantic_protocol.so`.

---

### 👤 Member 4 (M Janaki): P2P Wireless Transport & WFB-ng Protocol Lead
* **Domain:** Wireless Telecommunications, RF Protocol Engineering & Resilient P2P Networking
* **Mission:** Build a 100% offline, battle-tested radio transport stack adopting the WFB-ng protocol paradigm with Forward Error Correction (FEC), connectionless UDP datagrams, Libsodium encryption, and 7-hop mesh relay.

#### Exact Tools & Compilers:
* WFB-ng Architecture, Android Wi-Fi P2P (`WifiP2pManager`), Bluetooth Classic RFCOMM, BLE L2CAP, Reed-Solomon FEC, Libsodium (`crypto_aead_chacha20poly1305`), Java NIO Datagram Channels.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/java/org/isro/itantra/network/ReedSolomonFEC.kt`:** Block FEC generating 4 parity blocks for 8 data packets (survives 40% RF packet loss with zero lag).
2. **`app/src/main/java/org/isro/itantra/network/WifiP2pTransport.kt`:** Autonomous peer discovery, Group Owner negotiation, and high-throughput UDP socket server on port `8988`.
3. **`app/src/main/java/org/isro/itantra/network/WfbngTransportManager.kt`:** Master transceiver managing Libsodium encryption, FEC parity attachment, and $<50	ext{ ms}$ Bluetooth failover.
4. **`app/src/main/java/org/isro/itantra/network/MeshRelayRouter.kt`:** 7-hop store-and-forward relay extending range from 50m to 500m–5km.
5. **Deliverables:** `WfbngTransportManager.kt`, `ReedSolomonFEC.kt`, `WifiP2pTransport.kt`, `BluetoothTransport.kt`.

---

### 👤 Member 5 (Nupur): Native Android Core, State Machine & Database Systems Lead
* **Domain:** Android Native Architecture (NDK/JNI), Lifecycle Management & Edge Databases
* **Mission:** Build the master Android application architecture, manage the multi-threaded JNI bridge, run the 24/7 background radio daemon, and manage local SQLite storage.

#### Exact Tools & Compilers:
* Kotlin 1.9+, Android NDK r26c, CMake 3.22+, Room Persistence Library (SQLite 3.40+), Android Foreground Service, WakeLock API.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/cpp/native_bridge.cpp`:** High-performance JNI bindings with zero-copy `DirectByteBuffer` memory transfers.
2. **`app/src/main/java/org/isro/itantra/domain/PTTStateMachine.kt`:** Deterministic state machine + hardware volume button PTT interceptor (`KEYCODE_VOLUME_DOWN`).
3. **`app/src/main/java/org/isro/itantra/service/RadioDaemonService.kt`:** 24/7 Background Foreground Service with `START_STICKY` and `PARTIAL_WAKE_LOCK`.
4. **`app/src/main/java/org/isro/itantra/data/local/MessageDatabase.kt`:** Room Database implementing `MessageAuditLog`, `MeshPeerRegistry`, and `EmergencyCodebook`.
5. **Deliverables:** `native_bridge.cpp`, `RadioDaemonService.kt`, `PTTStateMachine.kt`, `MessageDatabase.kt`.

---

### 👤 Member 6 (Vaibhav Junior): Tactical UI/UX, Live Telemetry Dashboard & QA/Pitch Lead
* **Domain:** Modern Declarative UI, System Benchmarking, Quality Assurance & Hackathon Presentation
* **Mission:** Build the military-grade tactical UI, visual live telemetry monitor, energy profiling harness, and execute the 3-minute winning hackathon live pitch.

#### Exact Tools & Compilers:
* Jetpack Compose, Material Design 3, Android Studio Profiler (Energy, CPU, Memory), Battery Historian, JUnit 5.

#### Detailed Tasks & File Deliverables:
1. **`app/src/main/java/org/isro/itantra/ui/screens/MainWalkieTalkieScreen.kt`:** High-contrast tactical dark theme (`#0B0E14` with `#00E5FF` and `#FF3D00` accents).
2. **`app/src/main/java/org/isro/itantra/ui/components/TacticalPTTButton.kt` & `AudioWaveformVisualizer.kt`:** Central haptic PTT button with active dynamic audio FFT visualizer.
3. **`app/src/main/java/org/isro/itantra/ui/components/LiveTelemetryOverlay.kt`:** Real-time hardware telemetry card: `Payload: 6-38 Bytes | Airtime: 18 ms | Data Saved: 99.8% | Hops: 3 | Carrier: WFB-ng UDP`.
4. **`app/src/main/java/org/isro/itantra/ui/components/DemoInjectionDrawer.kt`:** Test drawer with one-touch triggers: `[Airplane Mode]`, `[Inject 40% Packet Loss]`, `[Trigger SOS Max Volume Alarm]`, `[Toggle Hindi -> Tamil]`.
5. **Deliverables:** `MainWalkieTalkieScreen.kt`, `LiveTelemetryOverlay.kt`, `Energy_CPU_Benchmark_Report.pdf`.

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

---

## 📅 10-Day Sprint Implementation Schedule

```
+----------------------------------------------------------------------------------------------------+
|                                    10-DAY SPRINT SCHEDULE                                          |
+----------------------------------------------------------------------------------------------------+

 Day 1 - 2: Foundation & Interfaces
 ├── M1 (Chhavi): Export Silero VAD & IndicConformer to ONNX; test desktop inference.
 ├── M2 (Vaibhav Senior): Export Indic FastPitch + HiFi-GAN to ONNX; verify speech synthesis.
 ├── M3 (Parth Karpe): Train Multi-Task TinyML model; define `packet_schema.proto`.
 ├── M4 (M Janaki): Build standalone Android Wi-Fi Direct discovery app with UDP sockets.
 ├── M5 (Nupur): Scaffold Android Studio monorepo with CMake NDK bridge and JNI stubs.
 └── M6 (Vaibhav Junior): Design high-contrast Figma UI assets and build Jetpack Compose theme.

 Day 3 - 5: Core Engineering & Quantization
 ├── M1 (Chhavi): Quantize STT model to INT8 (<38MB); integrate Oboe audio capture.
 ├── M2 (Vaibhav Senior): Quantize TTS model to INT8 (<45MB); implement `STREAM_ALARM` audio track.
 ├── M3 (Parth Karpe): Build IndicTrans2 translation bridge and 3-tier arithmetic tokenizer.
 ├── M4 (M Janaki): Implement Reed-Solomon FEC encoder/decoder + Libsodium ChaCha20 encryption.
 ├── M5 (Nupur): Build PTT state machine and foreground service lifecycle handlers.
 └── M6 (Vaibhav Junior): Implement real-time waveform visualizer and P2P peer radar screen.

 Day 6 - 7: Native Integration & JNI Fusion
 ├── Merge M1 (STT) + M2 (TTS) + M3 (TinyML) into native shared library (`libitantra_core.so`).
 ├── Connect M4 (WFB-ng Transport) to M5 (Foreground Service).
 ├── Connect M5 (JNI Engine) to M6 (Compose UI StateFlows).
 └── First full-loop on single phone: Speak -> VAD -> STT -> TinyML -> Packet -> TTS -> Speaker.

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

## 🎤 3-Minute Live Hackathon Winning Pitch Script

1. **Act 1: The Airplane Mode Proof (20s):**
   > *"Judges, we have placed both phones in complete Airplane Mode with zero internet, zero SIM cards, and zero cloud connectivity. Phone B is held across the room by the Chief Judge."*
2. **Act 2: Instant Voice Relay & Voice Cloning (40s):**
   > *(Speak into Phone A in Hindi)*: *"तोळनकेरे रोड पर 5 लोग फंसे हैं, तुरंत बोट भेजो!"*  
   > *(In <300ms, Phone B receives a 6-byte micro-packet, translates it to Tamil, and speaks aloud in the caller's pitch and panic urgency!)*  
   > *"That was a 99.9% bandwidth reduction transmitted over Janaki's WFB-ng radio link, with Parth's TinyML Agent resolving the local Tolankere landmark and Chhavi's pitch preserved."*
3. **Act 3: The 40% Noise & FEC Proof (40s):**
   > *(Tap "[Inject 40% Packet Loss]")* $ightarrow$ Speak another message $ightarrow$ Phone B still plays crystal-clear speech without any stutter!  
   > *"Our Reed-Solomon Forward Error Correction reconstructed the corrupted packets with zero retransmission lag."*
4. **Act 4: Emergency Mute Override & Battery Proof (20s):**
   > *(Put Phone B on Silent/DND)* $ightarrow$ Send SOS Alert $ightarrow$ Phone B overrides mute and blasts the alert at 100% volume via `STREAM_ALARM`.  
   > *(Point to the CPU monitor)*: *"While waiting for speech, our Silero VAD keeps CPU load under 2.8%, ensuring all-day field battery life."*
